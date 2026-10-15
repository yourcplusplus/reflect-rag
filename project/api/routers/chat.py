"""POST /api/v1/chat — SSE streaming chat backed by the existing RAG graph.

Flow of one turn:

1. resolve (or create) the conversation and persist the user message;
2. look the question up in Redis — an identical question with an identical
   conversation history is replayed from cache (TTL 1h) instead of re-running
   the graph;
3. otherwise stream the LangGraph run: node progress, tool calls, answer tokens;
4. persist the assistant message (with latency, intent, cache flag) and store
   the answer in Redis.

The blocking graph runs in a worker thread (:func:`api.services.rag_service.iter_blocking`),
so one slow generation never stalls the event loop, and the RAG lock serialises
turns against the shared models.
"""
from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.cache import RedisCache
from api.db import repository
from api.db.base import session_scope
from api.db.models import Conversation
from api.deps import AppState, database_unavailable, get_app_state, get_db
from api.schemas import ChatRequest
from api.services.rag_service import RagService, iter_blocking

logger = logging.getLogger("api.chat")

router = APIRouter(prefix="/api/v1", tags=["chat"])

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    # Ask reverse proxies (nginx, ...) not to buffer the stream.
    "X-Accel-Buffering": "no",
}
# How much of a cached answer is replayed per event; a plain answer otherwise
# arrives in one blob, which would look like a hung request to a browser.
CACHED_REPLAY_CHARS = 24
# Conversation history (messages) folded into the answer-cache key.
HISTORY_FINGERPRINT_MESSAGES = 10


def sse(event: str, data: dict) -> str:
    """Format one Server-Sent Event."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _persist_assistant(
    conversation_id: uuid.UUID,
    content: str,
    *,
    cached: bool,
    latency_ms: int,
    intent: str | None,
    error: str | None,
    meta: dict | None,
) -> str:
    """Write the answer in its own short-lived session (background-safe)."""
    with session_scope() as session:
        message = repository.add_assistant_message(
            session,
            conversation_id,
            content,
            cached=cached,
            latency_ms=latency_ms,
            intent=intent,
            error=error,
            meta=meta,
        )
        conversation = session.get(Conversation, conversation_id)
        if conversation is not None:
            repository.touch_conversation(session, conversation)
        return str(message.id)


@router.post(
    "/chat",
    summary="Stream an answer (SSE)",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": (
                "`text/event-stream`. Events in order: `conversation`, then "
                "`cache` (hit), `status` (warming up / queued), `node`, "
                "`tool_call`, `tool_result`, `tool_skipped`, `token`, `error` "
                "and finally `done`. Payload shapes are in the component "
                "schemas (`TokenEvent`, `DoneEvent`, ...)."
            ),
            "content": {"text/event-stream": {"schema": {"type": "string"}}},
        },
        404: {"description": "`conversation_id` does not exist."},
        503: {"description": "Database unavailable."},
    },
)
async def chat(
    payload: ChatRequest,
    request: Request,
    state: AppState = Depends(get_app_state),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    cache: RedisCache = state.cache
    service: RagService = state.service

    # --- 1. conversation + user message --------------------------------
    try:
        created = False
        if payload.conversation_id is not None:
            conversation = repository.get_conversation(db, payload.conversation_id)
            if conversation is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Conversation {payload.conversation_id} not found.",
                )
        else:
            conversation = repository.create_conversation(
                db, title=payload.message, meta={"origin": "api"}
            )
            created = True

        # Fingerprint of the history *before* this turn: a cached answer is only
        # replayed into a conversation whose context matches the one that
        # produced it.
        history = repository.recent_history(
            db, conversation.id, limit=HISTORY_FINGERPRINT_MESSAGES
        )
        repository.add_user_message(db, conversation.id, payload.message)
        repository.touch_conversation(db, conversation, title_hint=payload.message)
        db.commit()
        conversation_id = conversation.id
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise database_unavailable(exc) from exc

    cache_key = cache.answer_key(
        service.cache_namespace,
        payload.message,
        cache.history_fingerprint(history),
    )
    cache_enabled = bool(
        payload.use_cache and state.settings.answer_cache_enabled and cache.enabled
    )

    async def event_stream():
        started = time.perf_counter()
        yield sse(
            "conversation",
            {"conversation_id": str(conversation_id), "created": created},
        )

        # --- 2. cache lookup ------------------------------------------
        if cache_enabled:
            try:
                cached_payload = await asyncio.to_thread(cache.get_answer, cache_key)
            except Exception as exc:  # never fail a turn because of the cache
                logger.warning("Answer cache lookup failed: %s", exc)
                cached_payload = None
            if cached_payload and cached_payload.get("answer"):
                answer = str(cached_payload["answer"])
                meta = cached_payload.get("meta") or {}
                ttl = await asyncio.to_thread(cache.answer_ttl, cache_key)
                yield sse("cache", {"hit": True, "ttl_seconds": ttl})
                for offset in range(0, len(answer), CACHED_REPLAY_CHARS):
                    yield sse("token", {"text": answer[offset : offset + CACHED_REPLAY_CHARS]})
                latency_ms = round((time.perf_counter() - started) * 1000)
                message_id = await asyncio.to_thread(
                    _persist_assistant,
                    conversation_id,
                    answer,
                    cached=True,
                    latency_ms=latency_ms,
                    intent=meta.get("intent"),
                    error=None,
                    meta={"cache_key": cache_key, "source": "cache"},
                )
                yield sse(
                    "done",
                    {
                        "conversation_id": str(conversation_id),
                        "message_id": message_id,
                        "cached": True,
                        "latency_ms": latency_ms,
                        "intent": meta.get("intent"),
                        "chars": len(answer),
                        "outcome": "ok",
                        "tool_calls": 0,
                    },
                )
                return
            yield sse("cache", {"hit": False})

        # --- 3. wait for the RAG models, then stream the turn ----------
        if not service.ready and not service.initializing:
            # init is done but failed (initializing False + not ready)
            yield sse("error", {"detail": service.init_error or "RAG system is not ready"})
            yield sse(
                "done",
                {
                    "conversation_id": str(conversation_id),
                    "message_id": None,
                    "cached": False,
                    "latency_ms": round((time.perf_counter() - started) * 1000),
                    "intent": None,
                    "chars": 0,
                    "outcome": "error",
                    "tool_calls": 0,
                },
            )
            return

        waited = 0.0
        while service.initializing:
            if waited >= state.settings.rag_ready_timeout:
                yield sse(
                    "error",
                    {
                        "detail": (
                            "RAG system is still initializing after "
                            f"{state.settings.rag_ready_timeout}s; retry later."
                        )
                    },
                )
                return
            yield sse(
                "status",
                {"detail": "loading BGE-M3 / reranker / agent graph", "waited_s": round(waited, 1)},
            )
            await asyncio.sleep(3)
            waited += 3

        if service.busy:
            yield sse(
                "status",
                {"detail": "queued behind an in-flight request", "waited_s": 0.0},
            )
        if await request.is_disconnected():
            return

        cancelled = threading.Event()
        answer_parts: list[str] = []
        final: dict | None = None
        error_detail: str | None = None
        tool_calls = 0

        try:
            async for event in iter_blocking(
                lambda: service.stream_answer(payload.message, thread_id=conversation_id),
                cancelled,
            ):
                event_type = event.get("type")
                if event_type == "token":
                    answer_parts.append(event["text"])
                    yield sse("token", {"text": event["text"]})
                elif event_type == "node":
                    yield sse("node", {"node": event["node"], "text": event["text"]})
                elif event_type == "tool_call":
                    tool_calls += 1
                    yield sse(
                        "tool_call",
                        {"id": event["id"], "name": event["name"], "args": event["args"]},
                    )
                elif event_type == "tool_result":
                    yield sse(
                        "tool_result",
                        {"id": event["id"], "name": event["name"], "content": event["content"]},
                    )
                elif event_type == "tool_skipped":
                    yield sse("tool_skipped", {"id": event["id"], "name": event["name"]})
                elif event_type == "error":
                    error_detail = event["detail"]
                    yield sse("error", {"detail": event["detail"]})
                elif event_type == "final":
                    final = event
        except asyncio.CancelledError:  # client hung up mid-answer
            cancelled.set()
            raise
        finally:
            cancelled.set()

        answer = (final or {}).get("answer") or "".join(answer_parts).strip()
        intent = (final or {}).get("intent")
        outcome = (final or {}).get("outcome") or ("error" if error_detail else "ok")
        latency_ms = round((time.perf_counter() - started) * 1000)

        # --- 4. persist + cache ---------------------------------------
        message_id = await asyncio.to_thread(
            _persist_assistant,
            conversation_id,
            answer,
            cached=False,
            latency_ms=latency_ms,
            intent=intent,
            error=error_detail,
            meta={"tool_calls": tool_calls, "cache_key": cache_key, "outcome": outcome},
        )
        if answer and error_detail is None and cache_enabled:
            try:
                await asyncio.to_thread(
                    cache.set_answer,
                    cache_key,
                    answer,
                    ttl=state.settings.answer_cache_ttl,
                    meta={"intent": intent, "latency_ms": latency_ms},
                )
            except Exception as exc:  # cache writes must never break a turn
                logger.warning("Answer cache write failed: %s", exc)

        yield sse(
            "done",
            {
                "conversation_id": str(conversation_id),
                "message_id": message_id,
                "cached": False,
                "latency_ms": latency_ms,
                "intent": intent,
                "chars": len(answer),
                "outcome": outcome,
                "tool_calls": tool_calls,
            },
        )

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=SSE_HEADERS)
