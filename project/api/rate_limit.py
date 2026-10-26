"""Per-IP rate limiting for the chat endpoint, backed by Redis.

The counter is a fixed window: the Redis key embeds ``int(time() / window)``,
so a new key starts every window and the old one expires on its own. Each
request does ``INCR`` + ``EXPIRE`` in one pipeline — the two commands the
resume/deployment story calls for — and the key gets a TTL of two windows so a
crashed process can never leave a counter behind forever.

The middleware fails open. Redis is an optimisation elsewhere in the API
(answer/embedding cache) and it must stay one here: if it is down, requests are
served without a limit rather than turning an outage into a 500.

Only ``POST /api/v1/chat`` is limited. Everything else (health, docs, document
uploads) is left alone; uploads are protected by size limits, not frequency.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Awaitable, Callable

logger = logging.getLogger("api.ratelimit")

Scope = dict[str, Any]
Message = dict[str, Any]
Send = Callable[[Message], Awaitable[None]]


class RedisRateLimitMiddleware:
    """ASGI middleware: at most ``limit`` chat requests per IP per window."""

    def __init__(
        self,
        app: Callable[[Scope, Callable, Send], Awaitable[None]],
        *,
        limit: int = 30,
        window_seconds: int = 60,
        enabled: bool = True,
        path: str = "/api/v1/chat",
        trust_proxy: bool = False,
    ) -> None:
        self.app = app
        self.limit = max(1, int(limit))
        self.window_seconds = max(1, int(window_seconds))
        self.enabled = bool(enabled)
        self.path = path.rstrip("/") or "/"
        self.trust_proxy = bool(trust_proxy)

    async def __call__(self, scope: Scope, receive: Callable, send: Send) -> None:
        if not self._applies(scope):
            await self.app(scope, receive, send)
            return

        cache = self._cache(scope)
        if cache is None or not getattr(cache, "enabled", False):
            await self.app(scope, receive, send)
            return

        identity = self._client_ip(scope)
        count = await asyncio.to_thread(
            cache.hit_rate_limit,
            "chat",
            identity,
            window_seconds=self.window_seconds,
        )
        if count is None:  # Redis down: fail open
            await self.app(scope, receive, send)
            return

        remaining = max(0, self.limit - count)
        if count > self.limit:
            retry_after = self.window_seconds - int(time.time()) % self.window_seconds
            logger.warning(
                "Rate limit exceeded for %s (%s requests in %ss, limit %s)",
                identity,
                count,
                self.window_seconds,
                self.limit,
            )
            await self._reject(send, retry_after, remaining)
            return

        headers = [
            (b"x-ratelimit-limit", str(self.limit).encode()),
            (b"x-ratelimit-remaining", str(remaining).encode()),
            (b"x-ratelimit-window", str(self.window_seconds).encode()),
        ]
        await self.app(scope, receive, self._inject_headers(send, headers))

    # ----------------------------------------------------------------- helpers

    def _applies(self, scope: Scope) -> bool:
        if not self.enabled or scope.get("type") != "http":
            return False
        if scope.get("method") != "POST":
            return False
        path = str(scope.get("path") or "").rstrip("/") or "/"
        return path == self.path

    @staticmethod
    def _cache(scope: Scope) -> Any | None:
        app = scope.get("app")
        state = getattr(getattr(app, "state", None), "reflectrag", None)
        return getattr(state, "cache", None)

    def _client_ip(self, scope: Scope) -> str:
        if self.trust_proxy:
            for name, value in scope.get("headers") or []:
                if name.lower() == b"x-forwarded-for":
                    first = value.decode("latin-1").split(",")[0].strip()
                    if first:
                        return first
        client = scope.get("client")
        return str(client[0]) if client else "unknown"

    @staticmethod
    def _inject_headers(send: Send, headers: list[tuple[bytes, bytes]]) -> Send:
        async def sender(message: Message) -> None:
            if message.get("type") == "http.response.start":
                message = {
                    **message,
                    "headers": list(message.get("headers") or []) + headers,
                }
            await send(message)

        return sender

    async def _reject(self, send: Send, retry_after: int, remaining: int) -> None:
        body = json.dumps(
            {
                "detail": (
                    f"Rate limit exceeded: at most {self.limit} chat requests per "
                    f"{self.window_seconds}s per IP. Retry in {retry_after}s."
                ),
                "limit": self.limit,
                "window_seconds": self.window_seconds,
                "retry_after_seconds": retry_after,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        headers = [
            (b"content-type", b"application/json; charset=utf-8"),
            (b"content-length", str(len(body)).encode()),
            (b"retry-after", str(retry_after).encode()),
            (b"x-ratelimit-limit", str(self.limit).encode()),
            (b"x-ratelimit-remaining", str(remaining).encode()),
            (b"x-ratelimit-window", str(self.window_seconds).encode()),
        ]
        await send({"type": "http.response.start", "status": 429, "headers": headers})
        await send({"type": "http.response.body", "body": body})
