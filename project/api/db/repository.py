"""Database access helpers used by the routers.

Every function takes an explicit ``Session``; the request-scoped session comes
from :func:`api.deps.get_db`, and background writes (the assistant message at
the end of an SSE stream) open their own via :func:`api.db.base.session_scope`.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from api.db.models import (
    ROLE_ASSISTANT,
    ROLE_USER,
    Conversation,
    Document,
    Message,
)

TITLE_MAX_CHARS = 120
PREVIEW_MAX_CHARS = 200


@dataclass(slots=True)
class ConversationSummary:
    conversation: Conversation
    message_count: int
    last_message_at: datetime | None
    last_message_preview: str | None


# ---------------------------------------------------------------- health


def ping(session: Session) -> bool:
    """Cheap liveness probe for /health."""
    try:
        session.execute(text("SELECT 1"))
        return True
    except Exception:
        session.rollback()
        return False


# ----------------------------------------------------------- conversations


def create_conversation(session: Session, title: str | None = None, meta: dict[str, Any] | None = None) -> Conversation:
    conversation = Conversation(title=_clean_title(title), meta=meta)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


def get_conversation(session: Session, conversation_id: uuid.UUID) -> Conversation | None:
    return session.get(Conversation, conversation_id)


def delete_conversation(session: Session, conversation_id: uuid.UUID) -> bool:
    result = session.execute(delete(Conversation).where(Conversation.id == conversation_id))
    session.commit()
    return bool(result.rowcount)


def touch_conversation(session: Session, conversation: Conversation, *, title_hint: str | None = None) -> None:
    """Bump ``updated_at``; set the title from the first user message."""
    if not conversation.title and title_hint:
        conversation.title = _clean_title(title_hint)
    conversation.updated_at = func.now()
    session.add(conversation)


def list_conversations(session: Session, *, limit: int = 50, offset: int = 0) -> tuple[list[ConversationSummary], int]:
    last_message_at = (
        select(func.max(Message.created_at))
        .where(Message.conversation_id == Conversation.id)
        .correlate(Conversation)
        .scalar_subquery()
    )
    last_message_content = (
        select(Message.content)
        .where(Message.conversation_id == Conversation.id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(1)
        .correlate(Conversation)
        .scalar_subquery()
    )
    message_count = (
        select(func.count(Message.id))
        .where(Message.conversation_id == Conversation.id)
        .correlate(Conversation)
        .scalar_subquery()
    )
    rows = session.execute(
        select(Conversation, message_count, last_message_at, last_message_content)
        .order_by(Conversation.updated_at.desc(), Conversation.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    total = session.execute(select(func.count(Conversation.id))).scalar_one()
    return (
        [
            ConversationSummary(
                conversation=conversation,
                message_count=int(count or 0),
                last_message_at=last_at,
                last_message_preview=preview(last_content),
            )
            for conversation, count, last_at, last_content in rows
        ],
        int(total),
    )


# ---------------------------------------------------------------- messages


def add_message(
    session: Session,
    conversation_id: uuid.UUID,
    *,
    role: str,
    content: str,
    cached: bool = False,
    latency_ms: int | None = None,
    intent: str | None = None,
    error: str | None = None,
    meta: dict[str, Any] | None = None,
) -> Message:
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content or "",
        cached=cached,
        latency_ms=latency_ms,
        intent=intent,
        error=error,
        meta=meta,
    )
    session.add(message)
    session.flush()
    return message


def add_user_message(session: Session, conversation_id: uuid.UUID, content: str) -> Message:
    return add_message(session, conversation_id, role=ROLE_USER, content=content)


def add_assistant_message(
    session: Session,
    conversation_id: uuid.UUID,
    content: str,
    *,
    cached: bool = False,
    latency_ms: int | None = None,
    intent: str | None = None,
    error: str | None = None,
    meta: dict[str, Any] | None = None,
) -> Message:
    return add_message(
        session,
        conversation_id,
        role=ROLE_ASSISTANT,
        content=content,
        cached=cached,
        latency_ms=latency_ms,
        intent=intent,
        error=error,
        meta=meta,
    )


def list_messages(
    session: Session,
    conversation_id: uuid.UUID,
    *,
    limit: int | None = None,
    offset: int = 0,
    latest_first: bool = False,
) -> tuple[list[Message], int]:
    order = (Message.created_at.desc(), Message.id.desc()) if latest_first else (Message.created_at.asc(), Message.id.asc())
    stmt = select(Message).where(Message.conversation_id == conversation_id).order_by(*order)
    if offset:
        stmt = stmt.offset(offset)
    if limit:
        stmt = stmt.limit(limit)
    messages = list(session.execute(stmt).scalars())
    total = count_messages(session, conversation_id)
    return messages, total


def count_messages(session: Session, conversation_id: uuid.UUID, *, role: str | None = None) -> int:
    stmt = select(func.count(Message.id)).where(Message.conversation_id == conversation_id)
    if role:
        stmt = stmt.where(Message.role == role)
    return int(session.execute(stmt).scalar_one())


def recent_history(
    session: Session,
    conversation_id: uuid.UUID,
    *,
    limit: int = 10,
) -> list[tuple[str, str]]:
    """Last ``limit`` (role, content) pairs, oldest first.

    Used both as the answer-cache fingerprint and, indirectly, by the API's
    readiness contract — the graph keeps its own memory per thread id, so this
    is only about cache correctness.
    """
    rows = session.execute(
        select(Message.role, Message.content)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(limit)
    ).all()
    return [(role, content) for role, content in reversed(rows)]


# --------------------------------------------------------------- documents


def add_document(
    session: Session,
    *,
    filename: str,
    status: str,
    source_path: str | None = None,
    markdown_path: str | None = None,
    size_bytes: int | None = None,
    error: str | None = None,
    meta: dict[str, Any] | None = None,
) -> Document:
    document = Document(
        filename=filename,
        status=status,
        source_path=source_path,
        markdown_path=markdown_path,
        size_bytes=size_bytes,
        error=error,
        meta=meta,
    )
    session.add(document)
    session.flush()
    return document


def list_documents(
    session: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
) -> tuple[list[Document], int]:
    stmt = select(Document).order_by(Document.created_at.desc())
    count_stmt = select(func.count(Document.id))
    if status:
        stmt = stmt.where(Document.status == status)
        count_stmt = count_stmt.where(Document.status == status)
    documents = list(session.execute(stmt.limit(limit).offset(offset)).scalars())
    total = int(session.execute(count_stmt).scalar_one())
    return documents, total


def messages_by_conversation(session: Session, conversation_ids: Sequence[uuid.UUID]) -> dict[uuid.UUID, int]:
    """Message counts for a batch of conversations (used by the list endpoint)."""
    if not conversation_ids:
        return {}
    rows = session.execute(
        select(Message.conversation_id, func.count(Message.id))
        .where(Message.conversation_id.in_(list(conversation_ids)))
        .group_by(Message.conversation_id)
    ).all()
    return {conversation_id: int(count) for conversation_id, count in rows}


# ----------------------------------------------------------------- helpers


def _clean_title(title: str | None) -> str | None:
    if not title:
        return None
    collapsed = " ".join(title.split())
    return collapsed[:TITLE_MAX_CHARS] or None


def preview(content: str | None) -> str | None:
    """Collapse whitespace and truncate; used for list previews."""
    if not content:
        return None
    collapsed = " ".join(content.split())
    return collapsed[:PREVIEW_MAX_CHARS] or None


__all__ = [
    "ROLE_USER",
    "ROLE_ASSISTANT",
    "ConversationSummary",
    "add_assistant_message",
    "add_document",
    "add_message",
    "add_user_message",
    "count_messages",
    "create_conversation",
    "delete_conversation",
    "get_conversation",
    "list_conversations",
    "list_documents",
    "list_messages",
    "messages_by_conversation",
    "ping",
    "preview",
    "recent_history",
    "touch_conversation",
]
