"""Single-process consumer for the document ingest queue.

One worker, one loop, ``concurrency=1`` on purpose:

* the embedding model (BGE-M3) is the throughput bottleneck, so extra consumers
  would only compete for the same GPU;
* re-indexing one document must be serial (delete old chunks, write new ones),
  which a single consumer gives for free ().

The task state machine lives in PostgreSQL; Redis only carries the id. A crash
therefore never loses work — it leaves the id in ``processing`` and the next
start requeues it ().
"""
from __future__ import annotations

import logging
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone

from api.db import repository
from api.db.base import SessionLocal
from api.db.models import (
    STATUS_FAILED,
    STATUS_INDEXED,
    STATUS_INDEXING,
    STATUS_PENDING,
    STATUS_SKIPPED,
    Document,
)
from api.ingest.indexer import DocumentIndexer
from api.ingest.queue import IngestQueue
from api.settings import settings

logger = logging.getLogger("api.ingest.worker")

# Keep the error column readable; the full traceback goes to the log.
MAX_ERROR_CHARS = 1000


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:  # SQLite / naive columns
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class IngestWorker:
    """Consume ``doc:ingest:queue`` until stopped."""

    def __init__(self, app_settings=None, *, queue: IngestQueue | None = None,
                 indexer: DocumentIndexer | None = None) -> None:
        self.settings = app_settings or settings
        self.queue = queue or IngestQueue()
        self.indexer = indexer
        self.max_attempts = self.settings.ingest_max_attempts
        self.backoff_seconds = self.settings.ingest_backoff_seconds
        self.stale_after = timedelta(seconds=self.settings.ingest_stale_seconds)
        self._stop = threading.Event()
        self.processed = 0
        self.failed_tasks = 0

    # ------------------------------------------------------------- lifecycle

    def stop(self) -> None:
        """Ask the loop to exit after the current task (graceful shutdown)."""
        self._stop.set()

    def ensure_indexer(self) -> DocumentIndexer:
        # Loading BGE-M3 takes ~20s; building it before recovery also makes sure
        # the API's `alembic upgrade head` (compose) has finished by the time the
        # first row is touched. See docker-compose.yml.
        if self.indexer is None:
            self.indexer = DocumentIndexer(self.settings)
        return self.indexer

    def run_forever(self) -> None:
        self.ensure_indexer()
        try:
            recovered = self.recover()
            logger.info("startup recovery: %s", recovered)
        except Exception:
            logger.exception("startup recovery failed; continuing")

        logger.info(
            "ingest worker started: queue=%s processing=%s max_attempts=%s stale_after=%ss",
            self.settings.ingest_queue_key,
            self.settings.ingest_processing_key,
            self.max_attempts,
            self.settings.ingest_stale_seconds,
        )
        while not self._stop.is_set():
            try:
                outcome = self.run_once()
            except Exception:
                # Redis or PostgreSQL hiccup: keep the process alive; the id (if
                # any) stays in `processing` and is recovered once stale.
                logger.exception("worker loop error")
                self._stop.wait(2.0)
                continue
            if outcome != "idle":
                logger.info("task outcome: %s", outcome)
        logger.info(
            "ingest worker stopped (processed=%s failed=%s)", self.processed, self.failed_tasks
        )

    # --------------------------------------------------------------- recovery

    def recover(self) -> dict[str, int]:
        """崩溃恢复：processing 里的遗留任务按状态 ack / 重新入队。

        Called once at startup. A task is stale when it is ``indexing`` and its
        ``updated_at`` is older than ``INGEST_STALE_SECONDS`` — a fresh
        ``indexing`` row may belong to another live worker, so it is left alone.
        """
        stats = {"checked": 0, "requeued": 0, "acked": 0, "kept": 0}
        leftovers = self.queue.peek_processing()
        if not leftovers:
            return stats

        session = SessionLocal()
        try:
            for document_id in leftovers:
                stats["checked"] += 1
                try:
                    doc_uuid = uuid.UUID(document_id)
                except (ValueError, AttributeError):
                    logger.warning("dropping malformed queue id %r", document_id)
                    self.queue.ack(document_id)
                    stats["acked"] += 1
                    continue

                document = repository.get_document(session, doc_uuid)
                if document is None:
                    # The row was deleted while queued: nothing to resume.
                    self.queue.ack(document_id)
                    stats["acked"] += 1
                    continue

                if document.status in (STATUS_INDEXED, STATUS_SKIPPED):
                    self.queue.ack(document_id)
                    stats["acked"] += 1
                    continue

                if document.status == STATUS_FAILED:
                    # Parked as a business dead letter; a re-upload resets it.
                    self.queue.ack(document_id)
                    stats["acked"] += 1
                    continue

                if document.status == STATUS_INDEXING:
                    updated = _as_utc(document.updated_at)
                    is_stale = (
                        updated is None
                        or datetime.now(timezone.utc) - updated > self.stale_after
                    )
                    if is_stale:
                        repository.mark_document_pending(
                            session, document, error="recovered after a worker restart"
                        )
                        session.commit()
                        self.queue.requeue(document_id)
                        logger.warning(
                            "requeued stale task %s (indexing since %s)", document_id, updated
                        )
                        stats["requeued"] += 1
                    else:
                        stats["kept"] += 1
                    continue

                # pending (reserved, then crashed before indexing started)
                self.queue.requeue(document_id)
                stats["requeued"] += 1
        finally:
            session.close()
        return stats

    # -------------------------------------------------------------- main loop

    def run_once(self) -> str:
        """Reserve one task and process it. Returns an outcome tag."""
        # 手动 ACK 第一步：queue -> processing（阻塞等待 5s）
        document_id = self.queue.reserve()
        if document_id is None:
            return "idle"
        return self._process(document_id)

    def _process(self, document_id: str) -> str:
        session = SessionLocal()
        try:
            try:
                doc_uuid = uuid.UUID(document_id)
            except (ValueError, AttributeError):
                self.queue.ack(document_id)
                return "invalid-id"

            document: Document | None = repository.get_document(session, doc_uuid)
            if document is None:
                self.queue.ack(document_id)
                return "missing"

            # 幂等：重复投递（或重复入队）时已 indexed 直接跳过
            if document.status in (STATUS_INDEXED, STATUS_SKIPPED):
                self.queue.ack(document_id)
                return "skip-indexed"

            # 失败隔离：已达重试上限的 failed 文档不再消费（人工重放会重置状态）
            if document.status == STATUS_FAILED and (document.attempts or 0) >= self.max_attempts:
                self.queue.ack(document_id)
                return "skip-failed"

            # 状态机：先落 indexing 再干活，崩溃后 recover() 才能识别这条任务
            repository.mark_document_indexing(session, document)
            session.commit()

            try:
                result = self.ensure_indexer().index(document)
            except Exception as exc:
                logger.exception("indexing failed for %s (%s)", document_id, document.filename)
                session.rollback()
                document = repository.get_document(session, doc_uuid) or document
                summary = f"{type(exc).__name__}: {exc}"[:MAX_ERROR_CHARS]
                next_attempt = (document.attempts or 0) + 1

                if next_attempt < self.max_attempts:
                    # 还有预算：attempts+1 -> pending，重新入队并指数退避
                    repository.mark_document_retry(session, document, error=summary)
                    session.commit()
                    self.queue.requeue(document_id)
                    delay = self.backoff_seconds * (2 ** (next_attempt - 1))
                    if delay:
                        self._stop.wait(delay)
                    return f"retry({next_attempt}/{self.max_attempts})"

                # 预算用完：转业务死信，落 failed + error，人工重放
                repository.mark_document_failed(session, document, error=summary)
                session.commit()
                self.queue.ack(document_id)
                self.failed_tasks += 1
                return "failed"

            repository.mark_document_indexed(
                session, document, markdown_path=result.get("markdown_path")
            )
            session.commit()
            # 手动 ACK 第二步：真正成功后才从 processing 移除
            self.queue.ack(document_id)
            self.processed += 1
            return f"indexed({result.get('children', 0)} children)"
        except Exception:
            # Database/queue failure outside the indexing call: leave the id in
            # processing (it will be recovered once stale) and avoid a hot loop.
            session.rollback()
            raise
        finally:
            session.close()
