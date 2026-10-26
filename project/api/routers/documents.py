"""POST/GET /api/v1/documents — accept uploads, queue them, report progress.

Ingestion is asynchronous: ``POST`` only stores the file, writes a ``pending``
row and pushes the document id onto a Redis List; a separate ``worker.py``
process does PDF conversion, chunking, BGE-M3 embedding and the Qdrant write
(``api/ingest/``). Clients poll ``GET /api/v1/documents/{id}`` for the state
machine ``pending -> indexing -> indexed | failed``.

Why the split: parsing + embedding a paper takes tens of seconds and competes
with chat for the same GPU, so doing it inside the HTTP request made uploads
time out and blocked the RAG lock. Redis is only the transport; PostgreSQL holds
the task state and the idempotency key (file sha256).
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from api.db import repository
from api.db.models import (
    STATUS_FAILED,
    STATUS_INDEXED,
    STATUS_INDEXING,
    STATUS_PENDING,
    STATUS_SKIPPED,
    Document,
)
from api.deps import AppState, database_unavailable, get_app_state, get_db
from api.schemas import (
    DocumentEnqueueItem,
    DocumentEnqueueOut,
    DocumentListOut,
    DocumentOut,
    QueueStatsOut,
)

logger = logging.getLogger("api.documents")

router = APIRouter(prefix="/api/v1", tags=["documents"])

ALLOWED_SUFFIXES = {".pdf", ".md"}
UPLOAD_CHUNK_BYTES = 1024 * 1024
_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")

# Statuses that mean "this content is already known" — a re-upload is a no-op.
_DUPLICATE_TERMINAL = (STATUS_PENDING, STATUS_INDEXING, STATUS_INDEXED, STATUS_SKIPPED)


def _safe_filename(raw: str | None) -> str:
    """Strip directories and glob/path metacharacters from a client filename.

    The core's PDF converter globs the path it is given, so the stored name must
    not contain ``*?[]``; anything outside ``[A-Za-z0-9._-]`` becomes ``_``.
    """
    name = Path(raw or "").name
    name = _UNSAFE_FILENAME_CHARS.sub("_", name).strip("._")
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name is empty after sanitising.",
        )
    return name


def _unique_destination(directory: Path, filename: str) -> Path:
    destination = directory / filename
    if not destination.exists():
        return destination
    stem, suffix = Path(filename).stem, Path(filename).suffix
    for index in range(1, 1000):
        candidate = directory / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"Too many files named like {filename!r} in the upload directory.",
    )


async def _store_upload(
    upload: UploadFile, directory: Path, max_bytes: int
) -> tuple[Path, int, str | None, str]:
    """Stream the upload to disk and hash it on the way (sha256 = idempotency key)."""
    filename = _safe_filename(upload.filename)
    if Path(filename).suffix.lower() not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type {filename!r}; allowed: {sorted(ALLOWED_SUFFIXES)}.",
        )
    destination = _unique_destination(directory, filename)
    digest = hashlib.sha256()
    written = 0
    with destination.open("wb") as handle:
        while chunk := await upload.read(UPLOAD_CHUNK_BYTES):
            written += len(chunk)
            if written > max_bytes:
                handle.close()
                destination.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"{filename} exceeds the {max_bytes // (1024 * 1024)} MB upload limit.",
                )
            digest.update(chunk)
            handle.write(chunk)
    content_type = upload.content_type
    await upload.close()
    return destination, written, content_type, digest.hexdigest()


def _enqueue_item(document: Document, *, deduplicated: bool) -> DocumentEnqueueItem:
    return DocumentEnqueueItem(
        document_id=document.id,
        filename=document.filename,
        status=document.status,
        deduplicated=deduplicated,
    )


@router.post(
    "/documents",
    response_model=DocumentEnqueueOut,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload documents and queue them for indexing",
    responses={
        400: {"description": "Unsupported file type or empty file name."},
        413: {"description": "Upload exceeds MAX_UPLOAD_MB."},
        503: {"description": "Qdrant server mode or Redis queue is unavailable."},
    },
)
async def upload_documents(
    files: list[UploadFile] = File(..., description="PDF or Markdown files (.pdf, .md)."),
    state: AppState = Depends(get_app_state),
    db: Session = Depends(get_db),
) -> DocumentEnqueueOut:
    """异步边界：只落 pending + 投递任务，立即返回 202，不在请求里做解析/embedding。"""
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files uploaded.")
    # A separate worker process cannot share the embedded local Qdrant (it takes
    # an exclusive file lock), so async ingestion requires the server mode.
    if not state.settings.qdrant_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Async ingestion requires QDRANT_URL (Qdrant server mode): the worker "
                "process cannot share the embedded qdrant_db/. See docker-compose.yml."
            ),
        )

    upload_dir = state.settings.upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    max_bytes = state.settings.max_upload_mb * 1024 * 1024
    queue = state.ingest_queue

    stored: list[tuple[str, Path, int, str | None, str]] = []
    for upload in files:
        destination, size, content_type, digest = await _store_upload(upload, upload_dir, max_bytes)
        stored.append((destination.name, destination, size, content_type, digest))

    items: list[DocumentEnqueueItem] = []
    enqueue_failures: list[str] = []
    queued = 0
    deduplicated = 0

    for filename, path, size, content_type, digest in stored:
        try:
            existing = repository.find_document_by_hash(db, digest)

            # 幂等：同内容已登记（待处理/处理中/已完成）直接返回原 document_id
            if existing is not None and existing.status in _DUPLICATE_TERMINAL:
                if str(path) != (existing.source_path or ""):
                    path.unlink(missing_ok=True)  # discard the duplicate copy
                items.append(_enqueue_item(existing, deduplicated=True))
                deduplicated += 1
                continue

            if existing is not None and existing.status == STATUS_FAILED:
                # 失败文档允许重投：attempts 归零、清空 error、重新入队
                previous_path = existing.source_path
                repository.reset_document_for_reingest(
                    db,
                    existing,
                    source_path=str(path),
                    filename=filename,
                    size_bytes=size,
                    meta={"content_type": content_type},
                )
                db.commit()
                if previous_path and previous_path != str(path):
                    Path(previous_path).unlink(missing_ok=True)
                if await asyncio.to_thread(queue.enqueue, str(existing.id)):
                    items.append(_enqueue_item(existing, deduplicated=False))
                    queued += 1
                else:
                    repository.mark_document_enqueue_failed(
                        db, existing, error="投递队列失败"
                    )
                    db.commit()
                    enqueue_failures.append(filename)
                continue

            try:
                document = repository.add_document(
                    db,
                    filename=filename,
                    status=STATUS_PENDING,
                    source_path=str(path),
                    markdown_path=None,
                    size_bytes=size,
                    error=None,
                    meta={"content_type": content_type},
                    content_hash=digest,
                    task_id=uuid.uuid4().hex,
                    attempts=0,
                )
                db.commit()
            except IntegrityError:
                # Concurrent upload of the same bytes: the unique index won, but
                # the other request's row is the document to return.
                db.rollback()
                existing = repository.find_document_by_hash(db, digest)
                path.unlink(missing_ok=True)
                if existing is None:
                    raise
                items.append(_enqueue_item(existing, deduplicated=True))
                deduplicated += 1
                continue

            if await asyncio.to_thread(queue.enqueue, str(document.id)):
                items.append(_enqueue_item(document, deduplicated=False))
                queued += 1
            else:
                # Producer-side retries are exhausted: keep the row honest so a
                # re-upload can retry it instead of a phantom "pending" forever.
                repository.mark_document_enqueue_failed(
                    db, document, error="投递队列失败"
                )
                db.commit()
                enqueue_failures.append(filename)
        except SQLAlchemyError as exc:
            db.rollback()
            raise database_unavailable(exc) from exc

    logger.info(
        "enqueued upload: queued=%s deduplicated=%s enqueue_failures=%s",
        queued,
        deduplicated,
        enqueue_failures,
    )
    if enqueue_failures:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Failed to enqueue: " + ", ".join(enqueue_failures)
                + ". Those rows are marked failed with error '投递队列失败'; "
                "re-upload them once the queue is reachable."
            ),
        )

    return DocumentEnqueueOut(
        documents=items, queued=queued, deduplicated=deduplicated
    )


@router.get(
    "/documents",
    response_model=DocumentListOut,
    summary="List registered documents",
)
def list_documents(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    doc_status: str | None = Query(
        None, alias="status", description="Filter by indexing status."
    ),
    include_sources: bool = Query(
        True, description="Include the knowledge base's current source list."
    ),
    state: AppState = Depends(get_app_state),
    db: Session = Depends(get_db),
) -> DocumentListOut:
    try:
        documents, total = repository.list_documents(
            db, limit=limit, offset=offset, status=doc_status
        )
    except SQLAlchemyError as exc:
        db.rollback()
        raise database_unavailable(exc) from exc

    sources = [] if not include_sources else state.service.list_sources()
    return DocumentListOut(
        items=[DocumentOut.model_validate(document) for document in documents],
        total=total,
        limit=limit,
        offset=offset,
        indexed_sources=sources,
    )


@router.get(
    "/documents/{document_id}",
    response_model=DocumentOut,
    summary="Get one document's indexing state",
    responses={404: {"description": "Document not found."}},
)
def get_document(document_id: uuid.UUID, db: Session = Depends(get_db)) -> DocumentOut:
    """Poll target for the async state machine (pending -> indexing -> indexed/failed)."""
    try:
        document = repository.get_document(db, document_id)
    except SQLAlchemyError as exc:
        db.rollback()
        raise database_unavailable(exc) from exc
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Document {document_id} not found."
        )
    return DocumentOut.model_validate(document)


@router.get(
    "/queues/stats",
    response_model=QueueStatsOut,
    summary="Ingest queue depth and per-status document counts",
)
def queue_stats(state: AppState = Depends(get_app_state), db: Session = Depends(get_db)) -> QueueStatsOut:
    """积压观测：队列长度看 LLEN；真瓶颈在 embedding/Qdrant，不在队列。"""
    try:
        counts = repository.document_status_counts(db)
    except SQLAlchemyError as exc:
        db.rollback()
        raise database_unavailable(exc) from exc
    depths = state.ingest_queue.stats()
    return QueueStatsOut(
        queue_len=depths["queue_len"],
        processing_len=depths["processing_len"],
        pending_count=counts.get(STATUS_PENDING, 0),
        indexing_count=counts.get(STATUS_INDEXING, 0),
        indexed_count=counts.get(STATUS_INDEXED, 0),
        failed_count=counts.get(STATUS_FAILED, 0),
        skipped_count=counts.get(STATUS_SKIPPED, 0),
        max_attempts=state.settings.ingest_max_attempts,
        processing_key=state.settings.ingest_processing_key,
        queue_key=state.settings.ingest_queue_key,
    )
