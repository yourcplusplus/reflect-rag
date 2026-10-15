"""SQLAlchemy engine / session plumbing for the API database."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from api.settings import settings


class Base(DeclarativeBase):
    """Declarative base shared by the models and by Alembic's autogenerate."""


def _engine_kwargs(url: str) -> dict:
    kwargs: dict = {"pool_pre_ping": True, "future": True}
    if not url.startswith("sqlite"):
        kwargs.update(pool_size=5, max_overflow=5)
    return kwargs


# Engine creation does not connect, so importing this module never fails just
# because PostgreSQL is down; the first query does, and callers translate that
# into a 503 (see api/main.py).
engine = create_engine(
    settings.database_url,
    echo=settings.db_echo,
    **_engine_kwargs(settings.database_url),
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Session for code that runs outside a request (background writes)."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
