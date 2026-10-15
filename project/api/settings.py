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

        # --- Cache -------------------------------------------------------
        self.redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self.redis_enabled = _flag("REDIS_ENABLED", "true")
        self.answer_cache_enabled = _flag("ANSWER_CACHE_ENABLED", "true")
        self.embedding_cache_enabled = _flag("EMBEDDING_CACHE_ENABLED", "true")
        # 1h, per the API contract for high-frequency question answers.
        self.answer_cache_ttl = _int("ANSWER_CACHE_TTL", 3600)
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

        # --- RAG startup -------------------------------------------------
        # The RAG system loads BGE-M3 + the reranker (~2-4 GB) and the LangGraph
        # graph. Initialising it in the background keeps /docs and /health
        # answerable while the models warm up; set RAG_EAGER_INIT=true to block
        # startup on it instead.
        self.rag_eager_init = _flag("RAG_EAGER_INIT")
        self.rag_ready_timeout = _int("RAG_READY_TIMEOUT", 300)

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


settings = Settings()
