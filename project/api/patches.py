"""Runtime shims that let the API layer add behaviour the RAG core cannot.

Both shims are monkey-patches applied from ``api`` at startup, *before* the
``RAGSystem`` is built. They exist because the API layer is not allowed to
change ``core/``, ``rag_agent/`` or ``db/``:

1. :func:`install_embedding_cache` — wraps ``HuggingFaceEmbeddings.embed_query``
   / ``embed_documents`` with a Redis cache. ``db/vector_db_manager.py`` builds
   its embedder internally, so the class is the only seam available.
2. :func:`install_qdrant_server_shim` — redirects the ``QdrantClient(path=...)``
   constructor call in ``db/vector_db_manager.py`` to a Qdrant *server* when
   ``QDRANT_URL`` is set, which is what docker compose provides. Embedded
   local-mode Qdrant takes an exclusive file lock and cannot be shared between
   two processes (the Gradio app and the API), so a server is the only way to
   run both at once.

Neither patch touches behaviour when its feature is switched off: with no
``QDRANT_URL`` the client is constructed exactly as before, and if Redis is
down the embedding wrappers fall through to the real encoder.
"""
from __future__ import annotations

import logging
from typing import Any, Sequence

from api.cache import RedisCache

logger = logging.getLogger("api.patches")

_EMBEDDING_CACHE_INSTALLED = False
_QDRANT_SHIM_INSTALLED = False


def install_embedding_cache(cache: RedisCache, *, ttl: int) -> bool:
    """Cache dense embeddings in Redis.

    Dense embeddings (BGE-M3) are the expensive part of retrieval; the BM25
    sparse encoder and the cross-encoder reranker are left alone — the former is
    lexical and cheap, the latter is query-dependent and answers are already
    cached at a higher level (see the answer cache in ``routers/chat.py``).
    """
    global _EMBEDDING_CACHE_INSTALLED
    if _EMBEDDING_CACHE_INSTALLED:
        return True
    if not cache.enabled:
        logger.info("Embedding cache not installed (Redis disabled)")
        return False

    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except Exception as exc:  # pragma: no cover - langchain always present in this repo
        logger.warning("Embedding cache not installed: %s", exc)
        return False

    original_embed_query = HuggingFaceEmbeddings.embed_query
    original_embed_documents = HuggingFaceEmbeddings.embed_documents

    def _model_name(embedder) -> str:
        return str(getattr(embedder, "model_name", "unknown"))

    def embed_query(self, text: str) -> list[float]:
        model = _model_name(self)
        key = cache.embedding_key(model, text)
        cached = cache.get_embeddings([key])[0]
        if cached is not None:
            cache.count_embedding(hits=1, misses=0)
            return cached
        vector = original_embed_query(self, text)
        cache.set_embeddings([(key, vector)], ttl=ttl)
        cache.count_embedding(hits=0, misses=1)
        return vector

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        texts = list(texts)
        if not texts:
            return []
        model = _model_name(self)
        keys = [cache.embedding_key(model, text) for text in texts]
        cached_vectors = cache.get_embeddings(keys)

        missing = [i for i, vector in enumerate(cached_vectors) if vector is None]
        if missing:
            fresh = original_embed_documents(self, [texts[i] for i in missing])
            for position, vector in zip(missing, fresh):
                cached_vectors[position] = list(vector)
            cache.set_embeddings(
                ((keys[i], cached_vectors[i]) for i in missing), ttl=ttl
            )
        cache.count_embedding(hits=len(texts) - len(missing), misses=len(missing))
        return [list(vector) for vector in cached_vectors]  # type: ignore[arg-type]

    HuggingFaceEmbeddings.embed_query = embed_query
    HuggingFaceEmbeddings.embed_documents = embed_documents
    _EMBEDDING_CACHE_INSTALLED = True
    logger.info("Embedding cache installed (Redis %s, ttl=%ss)", cache.url, ttl)
    return True


def install_qdrant_server_shim(url: str) -> bool:
    """Make ``QdrantClient(path=...)`` talk to a Qdrant server instead.

    Only the keyword argument the core passes (``path=config.QDRANT_DB_PATH``)
    is rewritten; everything else — collection handling, sparse vectors, hybrid
    search — is unchanged, because it is the same ``QdrantClient`` class.
    """
    global _QDRANT_SHIM_INSTALLED
    if _QDRANT_SHIM_INSTALLED:
        return True
    if not url:
        return False

    from qdrant_client import QdrantClient

    original_init = QdrantClient.__init__

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if kwargs.get("path") is not None:
            kwargs.pop("path")
            kwargs.setdefault("url", url)
        original_init(self, *args, **kwargs)

    QdrantClient.__init__ = __init__  # type: ignore[method-assign]
    _QDRANT_SHIM_INSTALLED = True
    logger.info("Qdrant server shim installed -> %s", url)
    return True


def install_all(settings, cache: RedisCache) -> dict[str, Any]:
    """Apply every shim for this process. Called once, before RAG init."""
    applied: dict[str, Any] = {"qdrant_url": None, "embedding_cache": False}
    if settings.qdrant_url:
        applied["qdrant_url"] = settings.qdrant_url if install_qdrant_server_shim(settings.qdrant_url) else None
    if settings.embedding_cache_enabled:
        applied["embedding_cache"] = install_embedding_cache(cache, ttl=settings.embedding_cache_ttl)
    return applied
