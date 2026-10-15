"""ORM models: conversations, messages, documents.

Kept dialect-agnostic (``Uuid``/``JSON`` rather than the PostgreSQL-specific
types) so the test suite can run the same metadata against SQLite.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db.base import Base

ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
ROLES = (ROLE_USER, ROLE_ASSISTANT)

STATUS_INDEXED = "indexed"
STATUS_SKIPPED = "skipped"
STATUS_FAILED = "failed"


class Conversation(Base):
    """One chat session; ``id`` doubles as the LangGraph thread id."""

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Message.created_at",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Conversation {self.id} title={self.title!r}>"


class Message(Base):
    """A single turn; written by /api/v1/chat for both the user and the answer."""

    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_conversation_created", "conversation_id", "created_at"),
        Index("ix_messages_conversation_role", "conversation_id", "role"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Answer metadata, all optional: ``cached`` records a Redis answer-cache
    # hit, ``intent`` the router decision (simple_faq / single_hop / multi_hop),
    # ``latency_ms`` the wall-clock time of the turn, ``error`` a failed run.
    cached: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    intent: Mapped[str | None] = mapped_column(String(32), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    conversation: Mapped[Conversation] = relationship(back_populates="messages")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Message {self.role} {self.id} conversation={self.conversation_id}>"


class Document(Base):
    """Registry of documents pushed through POST /api/v1/documents."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    markdown_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=STATUS_INDEXED)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Document {self.filename} status={self.status}>"
