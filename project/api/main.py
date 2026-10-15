"""FastAPI entry point for the ReflectRAG service layer.

Run (from the repository root)::

    uvicorn api.main:app --app-dir project --host 0.0.0.0 --port 8000

or from ``project/``::

    uvicorn api.main:app

Configuration is environment-driven — see ``project/.env.example`` and
``api/settings.py``. The Gradio UI (``python project/app.py``) is unchanged and
can keep running on port 7860; note that both processes must agree on Qdrant:
the embedded local database takes an exclusive file lock, so run one process,
or point both at a Qdrant server via ``QDRANT_URL`` (what docker compose does).
"""
from __future__ import annotations

import logging
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

from api.settings import settings  # noqa: F401  (imported first: loads .env before the core)

# Make `config`, `core`, `rag_agent` and `db` importable when the process was
# started from the repository root (uvicorn --app-dir project does this too).
_PROJECT_DIR = str(Path(__file__).resolve().parents[1])
if _PROJECT_DIR not in sys.path:
    sys.path.insert(0, _PROJECT_DIR)

from fastapi import Depends, FastAPI, Request, Response, status  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from sqlalchemy.exc import SQLAlchemyError  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from api import __version__  # noqa: E402
from api.db import repository  # noqa: E402
from api.deps import DB_UNAVAILABLE_DETAIL, AppState, get_app_state, get_db  # noqa: E402
from api.routers import chat, conversations, documents  # noqa: E402
from api.schemas import CacheStatsOut, ComponentHealth, HealthOut  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger("api")

DESCRIPTION = """
REST service layer for ReflectRAG: streaming chat, document ingestion and
conversation history on top of the existing LangGraph agent.

* `POST /api/v1/chat` streams a turn as Server-Sent Events.
* `POST /api/v1/documents` indexes PDFs/Markdown; `GET` lists them.
* `GET /api/v1/conversations` lists persisted conversations.
* Answers are cached in Redis (TTL 1h) together with dense embeddings.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    state = AppState(settings)
    app.state.reflectrag = state
    logger.info("Starting API (qdrant=%s)", settings.qdrant_url or "embedded local mode")
    await state.startup()
    try:
        yield
    finally:
        await state.shutdown()
        logger.info("API stopped")


app = FastAPI(
    title="ReflectRAG API",
    description=DESCRIPTION,
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(conversations.router)


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.error("Unhandled database error on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": DB_UNAVAILABLE_DETAIL},
    )


@app.get("/", tags=["system"], summary="Service banner")
def root() -> dict:
    return {
        "name": "ReflectRAG API",
        "version": __version__,
        "docs": "/docs",
        "health": "/health",
        "endpoints": [
            "POST /api/v1/chat",
            "POST /api/v1/documents",
            "GET /api/v1/documents",
            "GET /api/v1/conversations",
        ],
    }


@app.get(
    "/health",
    response_model=HealthOut,
    tags=["system"],
    summary="Readiness and component health",
    responses={503: {"description": "RAG system not ready, or the database is unreachable."}},
)
def health(response: Response, state: AppState = Depends(get_app_state)) -> HealthOut:
    """Component health.

    ``status`` is ``initializing`` while the RAG models load (the server accepts
    requests immediately but cannot answer yet), ``degraded`` when only the
    optional Redis cache is down, ``error`` when a required component failed.
    The HTTP code is 503 until the RAG system is ready and the database answers,
    so it doubles as a container readiness probe.
    """
    components: dict[str, ComponentHealth] = {}

    rag_status = state.service.status()
    components["rag"] = ComponentHealth(
        ok=bool(rag_status["ready"]),
        detail=rag_status["error"] or ("ready" if rag_status["ready"] else "initializing"),
        extra={
            "collection": rag_status["collection"],
            "init_seconds": rag_status["init_seconds"],
            "busy": rag_status["busy"],
        },
    )

    # Database: a real connection round-trip, on a short-lived session.
    db_ok = False
    db_detail = "unreachable"
    try:
        from api.db.base import SessionLocal

        session: Session = SessionLocal()
        try:
            db_ok = repository.ping(session)
            db_detail = "ok" if db_ok else "unreachable"
        finally:
            session.close()
    except Exception as exc:
        db_detail = f"{type(exc).__name__}: {exc}"
    components["database"] = ComponentHealth(
        ok=db_ok,
        detail=db_detail,
        extra={
            "dialect": state.settings.database_url.split(":", 1)[0],
            "url": _redact_dsn(state.settings.database_url),
        },
    )

    cache_ok = state.cache.ping()
    components["redis"] = ComponentHealth(
        ok=cache_ok,
        detail="ok" if cache_ok else (state.cache.status.get("error") or "unreachable"),
        extra={"url": state.cache.url, "answer_cache_ttl": state.settings.answer_cache_ttl},
    )

    qdrant_extra = {"mode": "server" if state.settings.qdrant_url else "embedded"}
    qdrant_ok = rag_status["ready"]
    if rag_status["ready"]:
        try:
            vector_db = state.service.rag_system.vector_db
            collection = state.service.collection_name
            qdrant_extra["collection"] = collection
            qdrant_extra["points"] = vector_db.point_count(collection)
        except Exception as exc:
            qdrant_ok = False
            qdrant_extra["error"] = str(exc)
    components["qdrant"] = ComponentHealth(
        ok=qdrant_ok,
        detail=qdrant_extra.get("error") or ("ok" if qdrant_ok else "not ready"),
        extra=qdrant_extra,
    )

    if state.service.init_error:
        overall = "error"
    elif not rag_status["ready"]:
        overall = "initializing"
    elif not db_ok:
        overall = "error"
    elif not cache_ok:
        overall = "degraded"
    else:
        overall = "ok"

    response.status_code = (
        status.HTTP_200_OK if overall in {"ok", "degraded"} else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return HealthOut(
        status=overall,
        version=__version__,
        uptime_seconds=rag_status["uptime_seconds"],
        components=components,
    )


@app.get(
    "/api/v1/cache/stats",
    response_model=CacheStatsOut,
    tags=["system"],
    summary="Redis cache counters and key counts",
)
def cache_stats(state: AppState = Depends(get_app_state)) -> CacheStatsOut:
    stats = state.cache.stats()
    return CacheStatsOut(
        available=bool(stats.get("available")),
        url=stats.get("url", state.cache.url),
        counters=stats.get("counters", {}),
        hit_rate=stats.get("hit_rate", {}),
        keys=stats.get("keys", {}),
        ttl_seconds={
            "answer": state.settings.answer_cache_ttl,
            "embedding": state.settings.embedding_cache_ttl,
        },
        error=stats.get("error"),
    )


def _redact_dsn(dsn: str) -> str:
    """Hide the password of a connection URL before exposing it in /health."""
    if "@" not in dsn:
        return dsn
    scheme, rest = dsn.split("://", 1) if "://" in dsn else ("", dsn)
    credentials, host = rest.rsplit("@", 1)
    user = credentials.split(":", 1)[0]
    return f"{scheme}://{user}:***@{host}" if scheme else f"{user}:***@{host}"
