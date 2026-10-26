"""Redis List task queue for asynchronous document ingestion.

Two lists back the queue:

* ``doc:ingest:queue``      — document ids waiting to be indexed (LPUSH by the API)
* ``doc:ingest:processing`` — ids currently owned by a worker

``BRPOPLPUSH`` moves an id atomically from one list to the other, which is the
"reserve" half of a manual acknowledgement: a worker that dies mid-task leaves
the id in ``processing``, so the next start can put it back (consumer.recover()).

Only trusted, self-generated ids are queued, so the queue itself stays dumb:
durability and the task state machine live in PostgreSQL, not in Redis.
"""
from __future__ import annotations

import logging
import time

import redis

from api.settings import settings

logger = logging.getLogger("api.ingest.queue")


class IngestQueue:
    """Thin Redis List queue (producer + worker primitives)."""

    def __init__(
        self,
        url: str | None = None,
        *,
        queue_key: str | None = None,
        processing_key: str | None = None,
        poll_timeout: int | None = None,
        enqueue_retries: int | None = None,
        retry_delay: float | None = None,
    ) -> None:
        self.url = url or settings.redis_url
        self.queue_key = queue_key or settings.ingest_queue_key
        self.processing_key = processing_key or settings.ingest_processing_key
        self.poll_timeout = poll_timeout or settings.ingest_poll_timeout
        self.enqueue_retries = enqueue_retries or settings.ingest_enqueue_retries
        self.retry_delay = retry_delay if retry_delay is not None else settings.ingest_queue_retry_delay
        # BRPOPLPUSH blocks for poll_timeout, so the socket timeout must be larger.
        self._client = redis.Redis.from_url(
            self.url,
            decode_responses=True,
            socket_timeout=self.poll_timeout + 5,
            socket_connect_timeout=5,
            health_check_interval=30,
        )

    # ------------------------------------------------------------- producer

    def enqueue(self, document_id: str) -> bool:
        """异步边界：生产端只做一次 LPUSH，立刻返回，不等索引完成。

        Producer-side confirmation: if LPUSH fails the caller marks the row
        ``failed`` with "投递队列失败" instead of pretending it was queued.
        """
        for attempt in range(1, self.enqueue_retries + 1):
            try:
                self._client.lpush(self.queue_key, str(document_id))
                return True
            except Exception as exc:  # redis.RedisError / socket errors
                logger.warning(
                    "LPUSH %s failed (attempt %s/%s): %s",
                    self.queue_key,
                    attempt,
                    self.enqueue_retries,
                    exc,
                )
                if attempt < self.enqueue_retries and self.retry_delay:
                    time.sleep(self.retry_delay)
        return False

    # --------------------------------------------------------------- worker

    def reserve(self, timeout: int | None = None) -> str | None:
        """手动 ACK 第一步：原子地 queue -> processing，任务在处理期间仍可见。

        Returns None when the queue stayed empty for ``timeout`` seconds.
        """
        return self._client.brpoplpush(
            self.queue_key, self.processing_key, timeout or self.poll_timeout
        )

    def ack(self, document_id: str) -> None:
        """手动 ACK 第二步：业务真正成功（或明确跳过）后才移除 processing 标记。"""
        self._client.lrem(self.processing_key, 1, str(document_id))

    def requeue(self, document_id: str) -> bool:
        """重试：先撤掉 processing 标记，再放回队列，避免同一 id 同时留在两个 list。"""
        self.ack(document_id)
        return self.enqueue(document_id)

    def peek_processing(self) -> list[str]:
        """崩溃恢复用：查看所有"处理中"的任务。"""
        return list(self._client.lrange(self.processing_key, 0, -1))

    # ---------------------------------------------------------------- stats

    def stats(self) -> dict[str, int]:
        """积压观测：队列长度可直接 LLEN，不用扫 key。"""
        return {
            "queue_len": int(self._client.llen(self.queue_key)),
            "processing_len": int(self._client.llen(self.processing_key)),
        }

    def ping(self) -> bool:
        try:
            return bool(self._client.ping())
        except Exception:
            return False

    def close(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass
