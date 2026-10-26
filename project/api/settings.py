"""Settings for the REST API layer.

Loaded before anything from the RAG core is imported: ``project/.env`` must be
in the environment before ``huggingface_hub`` is imported, because that is when
``HF_ENDPOINT`` (the mirror this network needs) is read.

Nothing in this module mutates RAG behaviour: the core reads its own
configuration from ``project/config.py`` exactly as the Gradio app does.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# project/api/settings.py -> project/
PROJECT_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = PROJECT_DIR.parent


def _load_env_files() -> None:
    """Load .env files without overriding variables already in the environment.

    ``project/.env`` holds the RAG configuration shared with the Gradio app
    (DEEPSEEK_API_KEY, HF_ENDPOINT, ...); the repository root ``.env`` is what
    docker compose reads, so a checkout that only uses the API can keep its
    settings there. Existing environment variables always win, so container
    env vars are never clobbered by a stale file.
    """
    for path in (PROJECT_DIR / ".env", REPO_DIR / ".env"):
        if path.is_file():
            load_dotenv(path, override=False)


_load_env_files()


def _flag(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _list(name: str, default: str) -> list[str]:
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


class Settings:
    """Environment-backed configuration for the API service."""

    def __init__(self) -> None:
        self.project_dir = PROJECT_DIR
        self.repo_dir = REPO_DIR

        # --- Persistence -------------------------------------------------
        # psycopg 3 driver; the same URL is used by Alembic (project/api/migrations).
        self.database_url = os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://reflect:reflect@localhost:5432/reflect_rag",
        )
        self.db_echo = _flag("DB_ECHO")
        # LangGraph state store: "postgres" persists every conversation's
        # checkpoint (messages, pending clarification interrupts) across
        # restarts; "memory" is the in-process InMemorySaver (dev/tests).
        self.checkpoint_backend = (
            os.environ.get("CHECKPOINT_BACKEND", "postgres").strip().lower() or "postgres"
        )

        # --- Cache -------------------------------------------------------
        self.redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self.redis_enabled = _flag("REDIS_ENABLED", "true")
        self.answer_cache_enabled = _flag("ANSWER_CACHE_ENABLED", "true")
        self.embedding_cache_enabled = _flag("EMBEDDING_CACHE_ENABLED", "true")
        # 1h, per the API contract for high-frequency question answers.
        self.answer_cache_ttl = _int("ANSWER_CACHE_TTL", 3600)
        # Random 0..N seconds added to every answer TTL, so a burst of entries
        # written together does not all expire together (cache avalanche).
        self.answer_cache_ttl_jitter = max(0, min(300, _int("ANSWER_CACHE_TTL_JITTER", 300)))
        # Embeddings are deterministic, so the TTL only bounds staleness of a
        # changed model/index — a week is plenty.
        self.embedding_cache_ttl = _int("EMBEDDING_CACHE_TTL", 604800)
        self.cache_namespace = os.environ.get("CACHE_NAMESPACE", "reflectrag")

        # --- HTTP --------------------------------------------------------
        self.api_host = os.environ.get("API_HOST", "0.0.0.0")
        self.api_port = _int("API_PORT", 8000)
        self.cors_origins = _list("CORS_ORIGINS", "*")
        self.upload_dir = Path(os.environ.get("UPLOAD_DIR", str(REPO_DIR / "uploads")))
        self.max_upload_mb = _int("MAX_UPLOAD_MB", 50)

        # --- Rate limiting ------------------------------------------------
        # Per-IP window on POST /api/v1/chat, backed by Redis INCR + EXPIRE.
        self.rate_limit_enabled = _flag("RATE_LIMIT_ENABLED", "true")
        self.rate_limit_requests = max(1, _int("RATE_LIMIT_REQUESTS", 30))
        self.rate_limit_window_seconds = max(1, _int("RATE_LIMIT_WINDOW_SECONDS", 60))
        # Only enable behind a reverse proxy you control: X-Forwarded-For is
        # client-controlled otherwise and would make the limit trivial to spoof.
        self.rate_limit_trust_proxy = _flag("RATE_LIMIT_TRUST_PROXY")

        # --- LLM resilience ----------------------------------------------
        # tenacity: exponential backoff with jitter around every chat-model call.
        self.llm_retry_enabled = _flag("LLM_RETRY_ENABLED", "true")
        self.llm_max_attempts = max(1, _int("LLM_MAX_ATTEMPTS", 3))
        self.llm_retry_initial_wait = max(0.0, _float("LLM_RETRY_INITIAL_WAIT", 1.0))
        self.llm_retry_max_wait = max(0.0, _float("LLM_RETRY_MAX_WAIT", 20.0))
        self.llm_retry_jitter = max(0.0, _float("LLM_RETRY_JITTER", 2.0))
        # Returned (as a normal answer) when retries are exhausted, so a chat
        # turn degrades instead of surfacing an error/500.
        self.llm_fallback_message = os.environ.get(
            "LLM_FALLBACK_MESSAGE",
            "抱歉，模型服务暂时不可用，请稍后再试。",
        )

        # --- RAG startup -------------------------------------------------
        # The RAG system loads BGE-M3 + the reranker (~2-4 GB) and the LangGraph
        # graph. Initialising it in the background keeps /docs and /health
        # answerable while the models warm up; set RAG_EAGER_INIT=true to block
        # startup on it instead.
        self.rag_eager_init = _flag("RAG_EAGER_INIT")
        self.rag_ready_timeout = _int("RAG_READY_TIMEOUT", 300)
        # Embedded Qdrant is single-writer: if another process (e.g. the Gradio
        # app) holds the database, initialisation is retried instead of failing
        # permanently, so stopping that process is enough to recover.
        # 30 x 10s gives a 5-minute window at startup.
        self.rag_init_retry_attempts = _int("RAG_INIT_RETRY_ATTEMPTS", 30)
        self.rag_init_retry_delay = _int("RAG_INIT_RETRY_DELAY", 10)

        # --- Async document ingestion (Redis List queue) -------------------
        # POST /api/v1/documents only persists the row and pushes it onto a Redis
        # List; a separate worker.py process consumes it. See api/ingest/.
        self.ingest_queue_key = os.environ.get("INGEST_QUEUE_KEY", "doc:ingest:queue")
        self.ingest_processing_key = os.environ.get(
            "INGEST_PROCESSING_KEY", "doc:ingest:processing"
        )
        # Failed attempts before a document is parked as failed (business DLQ).
        self.ingest_max_attempts = max(1, _int("INGEST_MAX_ATTEMPTS", 3))
        # Exponential backoff between retries: 1s, 2s, 4s, ...
        self.ingest_backoff_seconds = max(0, _int("INGEST_BACKOFF_SECONDS", 1))
        # A task left in `processing` for longer than this is treated as the
        # leftover of a crashed worker and requeued on the next start.
        self.ingest_stale_seconds = max(60, _int("INGEST_STALE_SECONDS", 600))
        # BRPOPLPUSH blocking timeout: how long the worker waits for work.
        self.ingest_poll_timeout = max(1, _int("INGEST_POLL_TIMEOUT", 5))
        # Producer-side LPUSH retries before the row is marked failed.
        self.ingest_enqueue_retries = max(1, _int("INGEST_ENQUEUE_RETRIES", 3))
        self.ingest_queue_retry_delay = max(0.0, _float("INGEST_ENQUEUE_RETRY_DELAY", 0.2))

        # --- Qdrant ------------------------------------------------------
        # Empty -> the embedded local-mode DB the Gradio app uses. Set (e.g.
        # http://qdrant:6333 in docker compose) -> every QdrantClient(path=...)
        # call is redirected to the server. See api/patches.py.
        self.qdrant_url = os.environ.get("QDRANT_URL", "").strip()

    @property
    def allow_credentials(self) -> bool:
        # Browsers reject Allow-Credentials with a wildcard origin, and the API
        # is token-less, so credentials are only enabled for explicit origins.
        return "*" not in self.cors_origins

    @property
    def postgres_dsn(self) -> str:
        """``DATABASE_URL`` as a libpq DSN, for libraries that bypass SQLAlchemy.

        SQLAlchemy URLs carry the driver (``postgresql+psycopg://``); psycopg
        and LangGraph's PostgresSaver expect the plain ``postgresql://`` form.
        """
        url = self.database_url
        if "+" in url.split("://", 1)[0]:
            scheme, rest = url.split("://", 1)
            url = f"{scheme.split('+', 1)[0]}://{rest}"
        return url


settings = Settings()
