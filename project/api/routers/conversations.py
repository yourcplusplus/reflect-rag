"""GET /api/v1/conversations — read back what POST /api/v1/chat persisted."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.db import repository
from api.deps import database_unavailable, get_db
from api.schemas import (
    ConversationDetailOut,
    ConversationListOut,
    ConversationOut,
    MessageListOut,
    MessageOut,
)

router = APIRouter(prefix="/api/v1", tags=["conversations"])


def _summary_fields(summary: repository.ConversationSummary) -> dict:
    conversation = summary.conversation
    return {
        "id": conversation.id,
        "title": conversation.title,
        "summary": conversation.summary,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "message_count": summary.message_count,
        "last_message_at": summary.last_message_at,
        "last_message_preview": summary.last_message_preview,
    }


@router.get(
    "/conversations",
    response_model=ConversationListOut,
    summary="List conversations",
)
def list_conversations(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> ConversationListOut:
    try:
        summaries, total = repository.list_conversations(db, limit=limit, offset=offset)
    except SQLAlchemyError as exc:
        db.rollback()
        raise database_unavailable(exc) from exc

    return ConversationListOut(
        items=[ConversationOut(**_summary_fields(summary)) for summary in summaries],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetailOut,
    summary="Get one conversation with its messages",
    responses={404: {"description": "Conversation not found."}},
)
def get_conversation(
    conversation_id: uuid.UUID,
    limit: int | None = Query(None, ge=1, le=1000, description="Max messages to return."),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> ConversationDetailOut:
    try:
        conversation = repository.get_conversation(db, conversation_id)
        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found.",
            )
        messages, total = repository.list_messages(
            db, conversation_id, limit=limit, offset=offset
        )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise database_unavailable(exc) from exc

    last = messages[-1] if messages else None
    return ConversationDetailOut(
        id=conversation.id,
        title=conversation.title,
        summary=conversation.summary,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=total,
        last_message_at=last.created_at if last else None,
        last_message_preview=repository.preview(last.content) if last else None,
        messages=[MessageOut.model_validate(message) for message in messages],
    )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=MessageListOut,
    summary="List the messages of a conversation",
    responses={404: {"description": "Conversation not found."}},
)
def list_messages(
    conversation_id: uuid.UUID,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    latest_first: bool = Query(False, description="Newest message first."),
    db: Session = Depends(get_db),
) -> MessageListOut:
    try:
        if repository.get_conversation(db, conversation_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found.",
            )
        messages, total = repository.list_messages(
            db, conversation_id, limit=limit, offset=offset, latest_first=latest_first
        )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise database_unavailable(exc) from exc

    return MessageListOut(
        items=[MessageOut.model_validate(message) for message in messages],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a conversation and its messages",
    responses={404: {"description": "Conversation not found."}},
)
def delete_conversation(conversation_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    try:
        deleted = repository.delete_conversation(db, conversation_id)
    except SQLAlchemyError as exc:
        db.rollback()
        raise database_unavailable(exc) from exc
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found.",
        )
