"""Dependency injection: shared app state, DB session, Redis cache, RAG service.

The heavy singletons (cache client, RAG system) are built once in the lifespan
and hung off ``app.state``; the request-scoped dependency is only the DB
session, which stays scoped to one request.
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api import patches
from api.cache import RedisCache
from api.db.base import SessionLocal
from api.services.rag_service import RagService
from api.settings import Settings, settings

logger = logging.getLogger("api.deps")

DB_UNAVAILABLE_DETAIL = (
    "Database unavailable: check DATABASE_URL and that PostgreSQL is running "
    "(docker compose up -d postgres)."
)
RAG_NOT_READY_DETAIL = "RAG system is still initializing; poll /health and retry."


class AppState:
    """Everything the lifespan owns, reachable from `request.app.state`."""

    def __init__(self, app_settings: Settings | None = None) -> None:
        self.settings = app_settings or settings
        self.cache = RedisCache(
            self.settings.redis_url,
            namespace=self.settings.cache_namespace,
            enabled=self.settings.redis_enabled,
        )
        self.service = RagService()
        self.patches: dict = {}
        self.init_task: asyncio.Task | None = None

    # --- lifecycle ---------------------------------------------------------

    async def startup(self) -> None:
        # Redis is optional: a failed ping only disables caching.
        alive = await asyncio.to_thread(self.cache.ping)
        if not alive:
            logger.warning("Redis not reachable at %s — running without cache", self.settings.redis_url)

        # Patches must be installed before the RAGSystem is constructed: they
        # hook the embedding class and the Qdrant client the core builds.
        self.patches = await asyncio.to_thread(patches.install_all, self.settings, self.cache)
        logger.info("Startup patches: %s", self.patches or "none")

        if self.settings.rag_eager_init:
            await asyncio.to_thread(self.service.initialize)
            return
        # Default: keep serving /docs and /health while the models warm up.
        self.init_task = asyncio.create_task(
            asyncio.to_thread(self.service.initialize), name="rag-init"
        )

    async def shutdown(self) -> None:
        if self.init_task is not None and not self.init_task.done():
            try:
                await asyncio.wait_for(asyncio.shield(self.init_task), timeout=60)
            except Exception:
                logger.warning("RAG init did not finish before shutdown")
        await asyncio.to_thread(self.service.shutdown)
        await asyncio.to_thread(self.cache.close)


def get_app_state(request: Request) -> AppState:
    state = getattr(request.app.state, "reflectrag", None)
    if state is None:  # pragma: no cover - only if the lifespan did not run
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Application state is not initialized.",
        )
    return state


def get_cache(state: AppState = Depends(get_app_state)) -> RedisCache:
    return state.cache


def get_rag_service(state: AppState = Depends(get_app_state)) -> RagService:
    """The RAG service, or 503 while it is unusable.

    ``/chat`` does not use this dependency: it wants to answer with SSE events
    while the models warm up instead of a bare 503.
    """
    if state.service.init_error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"RAG system failed to initialize: {state.service.init_error}",
        )
    if not state.service.ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=RAG_NOT_READY_DETAIL,
            headers={"Retry-After": "10"},
        )
    return state.service


def get_db() -> Iterator[Session]:
    """Request-scoped SQLAlchemy session."""
    session = SessionLocal()
    try:
        yield session
    except SQLAlchemyError:
        session.rollback()
        raise
    finally:
        session.close()


def database_unavailable(exc: Exception) -> HTTPException:
    logger.error("Database error: %s", exc)
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=DB_UNAVAILABLE_DETAIL,
    )
