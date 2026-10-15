"""POST/GET /api/v1/documents — index documents and list what is indexed.

Uploads are written to ``UPLOAD_DIR`` (default ``<repo>/uploads``) and handed to
the core ``DocumentManager`` — the same chunking / embedding / parent-store path
the Gradio "Add Documents" tab uses. The result of every file is recorded in the
``documents`` table, while ``indexed_sources`` in the list response reports what
is actually in the knowledge base (which also covers documents indexed before
this API existed).
"""
from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.db import repository
from api.db.models import STATUS_FAILED, STATUS_INDEXED, STATUS_SKIPPED
from api.deps import AppState, database_unavailable, get_app_state, get_db, get_rag_service
from api.schemas import DocumentListOut, DocumentOut, DocumentUploadOut
from api.services.rag_service import RagService

logger = logging.getLogger("api.documents")

router = APIRouter(prefix="/api/v1", tags=["documents"])

ALLOWED_SUFFIXES = {".pdf", ".md"}
UPLOAD_CHUNK_BYTES = 1024 * 1024
_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


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


async def _store_upload(upload: UploadFile, directory: Path, max_bytes: int) -> tuple[Path, int, str | None]:
    filename = _safe_filename(upload.filename)
    if Path(filename).suffix.lower() not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type {filename!r}; allowed: {sorted(ALLOWED_SUFFIXES)}.",
        )
    destination = _unique_destination(directory, filename)
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
            handle.write(chunk)
    content_type = upload.content_type
    await upload.close()
    return destination, written, content_type


@router.post(
    "/documents",
    response_model=DocumentUploadOut,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and index documents",
    responses={400: {"description": "Unsupported file type or empty file name."}},
)
async def upload_documents(
    files: list[UploadFile] = File(..., description="PDF or Markdown files (.pdf, .md)."),
    state: AppState = Depends(get_app_state),
    service: RagService = Depends(get_rag_service),
    db: Session = Depends(get_db),
) -> DocumentUploadOut:
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files uploaded.")

    upload_dir = state.settings.upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    max_bytes = state.settings.max_upload_mb * 1024 * 1024

    stored: list[tuple[str, Path, int, str | None]] = []
    for upload in files:
        destination, size, content_type = await _store_upload(upload, upload_dir, max_bytes)
        stored.append((destination.name, destination, size, content_type))

    sources_before = set(await asyncio.to_thread(service.list_sources))
    added, skipped = await asyncio.to_thread(
        service.index_documents, [str(path) for _, path, _, _ in stored]
    )

    # The core reports only totals, so per-file status is derived from the
    # markdown files that appeared (or already existed) in the knowledge base.
    sources_after = set(await asyncio.to_thread(service.list_sources))
    # Directory the core converts uploads into (config.MARKDOWN_DIR).
    markdown_dir = getattr(service.document_manager, "markdown_dir", None)

    documents = []
    try:
        for filename, path, size, content_type in stored:
            markdown_name = f"{path.stem}.md"
            if markdown_name in sources_before:
                doc_status = STATUS_SKIPPED
            elif markdown_name in sources_after:
                doc_status = STATUS_INDEXED
            else:
                doc_status = STATUS_FAILED
            documents.append(
                repository.add_document(
                    db,
                    filename=filename,
                    status=doc_status,
                    source_path=str(path),
                    markdown_path=str(Path(markdown_dir) / markdown_name) if markdown_dir else None,
                    size_bytes=size,
                    error=None if doc_status != STATUS_FAILED else "Indexing failed; see server logs.",
                    meta={"content_type": content_type},
                )
            )
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise database_unavailable(exc) from exc

    logger.info(
        "Indexed upload: %s added, %s skipped, %s failed",
        added,
        skipped,
        sum(1 for document in documents if document.status == STATUS_FAILED),
    )
    return DocumentUploadOut(
        documents=[DocumentOut.model_validate(document) for document in documents],
        added=added,
        skipped=skipped,
        failed=sum(1 for document in documents if document.status == STATUS_FAILED),
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
