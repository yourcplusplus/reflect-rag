"""Turn one queued ``documents`` row into indexed child chunks.

The steps are exactly the ones the core ``DocumentManager`` performs for the
Gradio uploader (PDF -> markdown, parent/child chunking, parent-store write,
Qdrant write). They are called directly instead of through
``DocumentManager.add_documents`` because that method swallows exceptions and
only reports ``(added, skipped)`` — the queue needs the real exception to decide
between retrying and parking a document as failed.

Nothing under ``core/``, ``rag_agent/`` or ``db/`` is modified: this module only
orchestrates their public functions.
"""
from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import Any

import config
from api import patches
from api.settings import settings
from utils import pdfs_to_markdowns

logger = logging.getLogger("api.ingest.indexer")


class DocumentIndexer:
    """Indexing dependencies only — no LLM, no LangGraph, no reranker.

    A worker process therefore loads BGE-M3 + BM25 but not the chat stack, which
    keeps its memory footprint and GPU usage well below the API's.
    """

    def __init__(self, app_settings=None, *, vector_db: Any = None, parent_store: Any = None,
                 chunker: Any = None) -> None:
        self.settings = app_settings or settings
        # The core builds QdrantClient(path=...) internally; with QDRANT_URL set
        # the shim redirects it to the server so this process and the API share
        # one index. Installed here as well as in worker.py so the indexer is
        # safe to import from a script or a test.
        if self.settings.qdrant_url:
            patches.install_qdrant_server_shim(self.settings.qdrant_url)
        else:
            logger.warning(
                "QDRANT_URL is not set: falling back to the embedded local Qdrant. "
                "A separate worker needs the server mode to share the index with the API."
            )

        from db.parent_store_manager import ParentStoreManager
        from db.vector_db_manager import VectorDbManager
        from document_chunker import DocumentChunker

        self.vector_db = vector_db or VectorDbManager()
        self.parent_store = parent_store or ParentStoreManager()
        self.chunker = chunker or DocumentChunker()
        self.collection_name = self._resolve_collection_name()
        self._qdrant_client = None

    # ---------------------------------------------------------------- setup

    def _resolve_collection_name(self) -> str:
        """Same collection selection as ``RAGSystem.initialize``."""
        self.vector_db.create_collection(config.CHILD_COLLECTION)
        name = config.CHILD_COLLECTION
        if config.CONTEXTUAL_RETRIEVAL_ENABLED:
            contextual = config.CONTEXTUAL_COLLECTION
            if self.vector_db.collection_exists(contextual) and self.vector_db.point_count(contextual) > 0:
                name = contextual
        return name

    def _client(self):
        """Raw client for maintenance deletes (the vector store has no delete-by-filter)."""
        if self._qdrant_client is None:
            from qdrant_client import QdrantClient

            if self.settings.qdrant_url:
                self._qdrant_client = QdrantClient(url=self.settings.qdrant_url)
            else:
                self._qdrant_client = QdrantClient(path=config.QDRANT_DB_PATH)
        return self._qdrant_client

    # -------------------------------------------------------------- cleanup

    def _delete_points(self, source_name: str) -> None:
        from qdrant_client.http import models as qm

        self._client().delete(
            collection_name=self.collection_name,
            points_selector=qm.Filter(
                must=[qm.FieldCondition(key="metadata.source", match=qm.MatchValue(value=source_name))]
            ),
            wait=True,
        )

    def _delete_parents(self, source_name: str) -> int:
        """Delete parent chunks of one source.

        ``ParentStoreManager`` only offers delete-by-parent-id, so the store is
        scanned by metadata (same approach as its own ``list_sources``).
        """
        removed = 0
        for path in Path(config.PARENT_STORE_PATH).glob("*.json"):
            try:
                meta = json.loads(path.read_text(encoding="utf-8")).get("metadata", {})
            except (OSError, json.JSONDecodeError):
                continue
            if meta.get("source") == source_name:
                path.unlink(missing_ok=True)
                removed += 1
        return removed

    def purge(self, source_name: str, markdown_path: Path | None = None) -> None:
        """顺序：同一文档重建时先删旧 chunk，再写新 chunk，避免新旧两份并存。"""
        self._delete_points(source_name)
        self._delete_parents(source_name)
        if markdown_path is not None and markdown_path.exists():
            markdown_path.unlink(missing_ok=True)

    # ---------------------------------------------------------------- index

    def index(self, document: Any) -> dict[str, Any]:
        """Index one document row; raises on any failure (the worker retries)."""
        source_path = Path(document.source_path or "")
        if not source_path.is_file():
            raise FileNotFoundError(f"upload file is gone: {source_path}")

        markdown_dir = Path(config.MARKDOWN_DIR)
        markdown_dir.mkdir(parents=True, exist_ok=True)
        markdown_path = markdown_dir / f"{source_path.stem}.md"
        source_name = source_path.name

        # 单 worker + 单队列 => 同一文档的重建天然串行；这里再做一次先删后写
        self.purge(source_name, markdown_path)

        try:
            if source_path.suffix.lower() == ".md":
                shutil.copy(source_path, markdown_path)
            else:
                pdfs_to_markdowns(str(source_path), overwrite=False)
                if not markdown_path.exists():
                    raise RuntimeError("PDF conversion produced no markdown output")

            parents, children = self.chunker.create_chunks_single(
                markdown_path, source_name=source_name
            )
            if not children:
                raise ValueError("No child chunks were created")

            self.parent_store.save_many(parents)
            collection = self.vector_db.get_collection(self.collection_name)
            collection.add_documents(children)
        except Exception:
            # 幂等：失败时清掉半成品，重试不会叠加重复 chunk
            try:
                self.purge(source_name, markdown_path)
            except Exception:  # cleanup must not mask the original error
                logger.warning("cleanup after failed indexing also failed for %s", source_name, exc_info=True)
            raise

        logger.info(
            "indexed %s: %s parents, %s children into %s",
            source_name,
            len(parents),
            len(children),
            self.collection_name,
        )
        return {
            "source": source_name,
            "parents": len(parents),
            "children": len(children),
            "markdown_path": str(markdown_path),
        }

    def close(self) -> None:
        if self._qdrant_client is not None:
            try:
                self._qdrant_client.close()
            except Exception:
                pass
