"""Redis-backed caches: high-frequency answers and dense embeddings.

Design notes
------------
* **Fail open.** Redis is an optimisation, never a dependency: every operation
  is guarded, and a failure marks the client "down" for a short window so a
  dead Redis does not add a connection timeout to every request.
* **Content-addressed keys.** Answers are keyed on the question *plus* a
  fingerprint of the conversation history that produced them, so a cached
  answer can never be replayed into a conversation with different context.
  Embeddings are keyed on model + text.
* **Counters.** Hit/miss counters live in Redis so cache effectiveness is
  observable (`GET /api/v1/cache/stats`), which is also how the cache is
  verified end to end.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any, Iterable, Sequence

import redis

logger = logging.getLogger("api.cache")

ANSWER_PREFIX = "answer"
EMBEDDING_PREFIX = "embedding"
STATS_PREFIX = "stats"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class RedisCache:
    """Thin, fail-open wrapper around a Redis connection."""

    def __init__(
        self,
        url: str,
        *,
        namespace: str = "reflectrag",
        enabled: bool = True,
        socket_timeout: float = 2.0,
    ) -> None:
        self.url = url
        self.namespace = namespace
        self.enabled = bool(enabled and url)
        self._client: redis.Redis | None = None
        self._down_until = 0.0
        self._down_reason: str | None = None
        self.last_error: str | None = None
        if self.enabled:
            # decode_responses=True: values are JSON text, so they stay readable
            # with redis-cli while debugging.
            self._client = redis.Redis.from_url(
                url,
                decode_responses=True,
                socket_timeout=socket_timeout,
                socket_connect_timeout=socket_timeout,
                health_check_interval=30,
            )

    # ------------------------------------------------------------------ state

    @property
    def available(self) -> bool:
        return self._client is not None and time.monotonic() >= self._down_until

    @property
    def status(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "available": self.available,
            "url": self.url,
            "error": self._down_reason,
        }

    def _trip(self, exc: Exception) -> None:
        self._down_until = time.monotonic() + 30.0
        self._down_reason = f"{type(exc).__name__}: {exc}"
        if self.last_error != self._down_reason:
            logger.warning("Redis unavailable, caching disabled for 30s (%s)", self._down_reason)
            self.last_error = self._down_reason

    def _call(self, fn, *args, **kwargs):
        """Run a Redis command; return None (and trip the breaker) on failure."""
        if not self.available:
            return None
        try:
            result = fn(*args, **kwargs)
            if self._down_reason is not None:
                logger.info("Redis recovered")
                self._down_reason = None
            return result
        except Exception as exc:  # redis.RedisError + socket errors
            self._trip(exc)
            return None

    def ping(self) -> bool:
        return self._call(self._client.ping) is True if self._client is not None else False

    def close(self) -> None:
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass

    # ------------------------------------------------------------------- keys

    def _key(self, prefix: str, *parts: str) -> str:
        return ":".join([self.namespace, prefix, *parts])

    def answer_key(self, namespace: str, question: str, history_fingerprint: str = "") -> str:
        """Key for one (namespace, question, conversation-history) triple."""
        digest = _sha256(f"{namespace}\x00{question.strip()}\x00{history_fingerprint}")
        return self._key(ANSWER_PREFIX, namespace, digest)

    def embedding_key(self, model: str, text: str) -> str:
        return self._key(EMBEDDING_PREFIX, model, _sha256(text))

    # ---------------------------------------------------------------- answers

    def get_answer(self, key: str) -> dict[str, Any] | None:
        raw = self._call(self._client.get, key) if self._client is not None else None
        if raw is None:
            self._count("answer_misses")
            return None
        try:
            payload = json.loads(raw)
        except (TypeError, ValueError):
            self._count("answer_misses")
            return None
        self._count("answer_hits")
        return payload if isinstance(payload, dict) else None

    def set_answer(self, key: str, answer: str, *, ttl: int, meta: dict[str, Any] | None = None) -> bool:
        payload = json.dumps({"answer": answer, "meta": meta or {}}, ensure_ascii=False)
        ok = self._call(self._client.set, key, payload, ex=ttl) if self._client is not None else None
        return bool(ok)

    def peek_answer(self, key: str) -> dict[str, Any] | None:
        """Read without touching the hit/miss counters (used by tests/tools)."""
        if not self.available or self._client is None:
            return None
        try:
            raw = self._client.get(key)
            return json.loads(raw) if raw else None
        except Exception as exc:
            self._trip(exc)
            return None

    def answer_ttl(self, key: str) -> int:
        ttl = self._call(self._client.ttl, key) if self._client is not None else None
        return int(ttl) if isinstance(ttl, int) else -2

    # ------------------------------------------------------------- embeddings

    def get_embeddings(self, keys: Sequence[str]) -> list[list[float] | None]:
        """MGET embeddings; a miss is None (not a counter miss)."""
        if not keys:
            return []
        if not self.available or self._client is None:
            return [None] * len(keys)
        raw_values = self._call(self._client.mget, list(keys))
        if raw_values is None:
            return [None] * len(keys)
        out: list[list[float] | None] = []
        for raw in raw_values:
            if raw is None:
                out.append(None)
                continue
            try:
                vector = json.loads(raw)
                out.append([float(x) for x in vector] if isinstance(vector, list) else None)
            except (TypeError, ValueError):
                out.append(None)
        return out

    def set_embeddings(self, items: Iterable[tuple[str, Sequence[float]]], *, ttl: int) -> int:
        """Pipeline writes for a batch of embeddings. Returns the number written."""
        if not self.available or self._client is None:
            return 0
        payloads = [(key, json.dumps([float(x) for x in vector])) for key, vector in items]
        if not payloads:
            return 0
        try:
            pipe = self._client.pipeline(transaction=False)
            for key, payload in payloads:
                if ttl > 0:
                    pipe.set(key, payload, ex=ttl)
                else:
                    pipe.set(key, payload)
            pipe.execute()
            return len(payloads)
        except Exception as exc:
            self._trip(exc)
            return 0

    def count_embedding(self, hits: int, misses: int) -> None:
        if hits:
            self._count("embedding_hits", hits)
        if misses:
            self._count("embedding_misses", misses)

    # ------------------------------------------------------------------ stats

    def _count(self, name: str, amount: int = 1) -> None:
        if self._client is not None:
            self._call(self._client.incrby, self._key(STATS_PREFIX, name), amount)

    def stats(self, prefix: str = ANSWER_PREFIX, sample_limit: int = 5000) -> dict[str, Any]:
        if not self.available or self._client is None:
            return {"available": False, "url": self.url, "error": self._down_reason}
        counters = {
            name: int(self._call(self._client.get, self._key(STATS_PREFIX, name)) or 0)
            for name in ("answer_hits", "answer_misses", "embedding_hits", "embedding_misses")
        }
        keys = [
            name
            for name in (
                self._key(ANSWER_PREFIX),
                self._key(EMBEDDING_PREFIX),
            )
        ]
        counts: dict[str, int] = {}
        for base in keys:
            counts[base.rsplit(":", 1)[-1]] = self._scan_count(base + ":*", sample_limit)
        answer_hits = counters["answer_hits"]
        answer_total = answer_hits + counters["answer_misses"]
        embed_hits = counters["embedding_hits"]
        embed_total = embed_hits + counters["embedding_misses"]
        return {
            "available": True,
            "url": self.url,
            "counters": counters,
            "hit_rate": {
                "answer": round(answer_hits / answer_total, 4) if answer_total else None,
                "embedding": round(embed_hits / embed_total, 4) if embed_total else None,
            },
            "keys": counts,
        }

    def _scan_count(self, pattern: str, sample_limit: int) -> int:
        if self._client is None:
            return 0
        total = 0
        try:
            cursor = 0
            while True:
                cursor, batch = self._client.scan(cursor=cursor, match=pattern, count=500)
                total += len(batch)
                if cursor == 0 or total >= sample_limit:
                    break
        except Exception as exc:
            self._trip(exc)
        return total

    @staticmethod
    def history_fingerprint(messages: Sequence[tuple[str, str]]) -> str:
        """Fingerprint of the conversation history an answer depends on."""
        if not messages:
            return ""
        joined = "\n".join(f"{role}:{content}" for role, content in messages)
        return _sha256(joined)
