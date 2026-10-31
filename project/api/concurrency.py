"""Process-local singleflight locks keyed by a cache key.

Why this exists
---------------
The answer cache is checked before generation, but two identical requests that
miss at the same time would both run the whole RAG graph. The lock below makes
the *second* caller wait, then re-check the cache: the leader writes the answer
before releasing, so followers normally serve it from Redis without a second
generation. That is the "cache breakdown" (击穿) guard.

Scope
-----
The locks live in one process/event loop. They serialize duplicate questions,
not all questions (the RAG generation lock still does that), and they are not
distributed: a second API instance needs a shared lock (Redis SET NX PX or a
fencing-token scheme) to get the same guarantee across processes.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator


class KeyedLocks:
    """``asyncio.Lock`` per key, removed once nobody holds or waits on it."""

    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}
        self._users: dict[str, int] = {}
        self._guard = asyncio.Lock()

    @asynccontextmanager
    async def hold(self, key: str) -> AsyncIterator[None]:
        async with self._guard:
            lock = self._locks.get(key)
            if lock is None:
                lock = asyncio.Lock()
                self._locks[key] = lock
            self._users[key] = self._users.get(key, 0) + 1
        try:
            async with lock:
                yield
        finally:
            async with self._guard:
                remaining = self._users.get(key, 1) - 1
                if remaining > 0:
                    self._users[key] = remaining
                else:
                    self._users.pop(key, None)
                    self._locks.pop(key, None)

    def active_keys(self) -> int:
        """Number of keys currently held or awaited (for tests/observability)."""
        return len(self._locks)
