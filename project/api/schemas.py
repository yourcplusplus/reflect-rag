"""Pydantic request/response models for the API.

The SSE payloads of ``POST /api/v1/chat`` are modelled here too (``TokenEvent``,
``ToolCallEvent``, ...) so the event contract shows up in the generated OpenAPI
schema, even though the endpoint itself streams plain ``text/event-stream``
lines rather than a validated response body.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Role = Literal["user", "assistant"]
DocumentStatus = Literal["indexed", "skipped", "failed"]
HealthStatus = Literal["ok", "degraded", "initializing", "error"]
ChatOutcome = Literal["ok", "error", "cancelled"]


# --------------------------------------------------------------------- chat


class ChatRequest(BaseModel):
    """One chat turn. The answer comes back as an SSE stream."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=8000,
        description="User question. Re-sending a message to a conversation that is "
        "waiting for clarification continues that turn.",
        examples=["What are the main contributions of the BGE-M3 paper?"],
    )
    conversation_id: uuid.UUID | None = Field(
        default=None,
        description="Existing conversation to continue. Omit to start a new one; "
        "the created id is reported in the `conversation` SSE event.",
    )
    use_cache: bool = Field(
        default=True,
        description="Consult/refresh the Redis answer cache (TTL 1h). Set false to force a fresh run.",
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {"message": "What is hybrid retrieval?", "use_cache": True}
        },
    )


class ChatEventBase(BaseModel):
    """Base class for the SSE event payloads documented below."""

    event: str


class StatusEvent(ChatEventBase):
    event: Literal["status"] = "status"
    detail: str
    waited_s: float | None = None


class ConversationEvent(ChatEventBase):
    event: Literal["conversation"] = "conversation"
    conversation_id: uuid.UUID
    created: bool


class CacheEvent(ChatEventBase):
    event: Literal["cache"] = "cache"
    hit: bool
    ttl_seconds: int | None = None


class NodeEvent(ChatEventBase):
    event: Literal["node"] = "node"
    node: str = Field(description="Graph node, e.g. rewrite_query / summarize_history.")
    text: str = Field(description="Accumulated node output so far.")


class ToolCallEvent(ChatEventBase):
    event: Literal["tool_call"] = "tool_call"
    id: str
    name: str
    args: dict[str, Any] = Field(default_factory=dict)


class ToolResultEvent(ChatEventBase):
    event: Literal["tool_result"] = "tool_result"
    id: str
    name: str
    content: str


class ToolSkippedEvent(ChatEventBase):
    event: Literal["tool_skipped"] = "tool_skipped"
    id: str
    name: str = Field(description="Tool whose call was skipped: research budget exceeded.")


class TokenEvent(ChatEventBase):
    event: Literal["token"] = "token"
    text: str


class ErrorEvent(ChatEventBase):
    event: Literal["error"] = "error"
    detail: str


class DoneEvent(ChatEventBase):
    event: Literal["done"] = "done"
    conversation_id: uuid.UUID
    message_id: uuid.UUID | None = Field(
        default=None, description="Persisted assistant message; null when the turn failed."
    )
    cached: bool
    latency_ms: int
    intent: str | None = None
    chars: int
    outcome: ChatOutcome
    tool_calls: int = 0


# ----------------------------------------------------------------- messages


class MessageOut(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: Role
    content: str
    cached: bool = False
    latency_ms: int | None = None
    intent: str | None = None
    error: str | None = None
    meta: dict[str, Any] | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------ conversations


class ConversationOut(BaseModel):
    id: uuid.UUID
    title: str | None = None
    summary: str | None = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    last_message_at: datetime | None = None
    last_message_preview: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ConversationListOut(BaseModel):
    items: list[ConversationOut]
    total: int
    limit: int
    offset: int


class ConversationDetailOut(ConversationOut):
    messages: list[MessageOut] = Field(default_factory=list)


class MessageListOut(BaseModel):
    items: list[MessageOut]
    total: int
    limit: int | None = None
    offset: int = 0


# --------------------------------------------------------------- documents


class DocumentOut(BaseModel):
    id: uuid.UUID
    filename: str
    status: DocumentStatus
    source_path: str | None = None
    markdown_path: str | None = None
    size_bytes: int | None = None
    error: str | None = None
    meta: dict[str, Any] | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentListOut(BaseModel):
    items: list[DocumentOut]
    total: int
    limit: int
    offset: int
    indexed_sources: list[str] = Field(
        default_factory=list,
        description="Files currently present in the knowledge base (parent store). "
        "Lets clients see documents indexed before this API existed.",
    )


class DocumentUploadOut(BaseModel):
    documents: list[DocumentOut]
    added: int = Field(description="Files newly chunked + embedded.")
    skipped: int = Field(description="Files already in the knowledge base.")
    failed: int = Field(description="Files that could not be processed.")


# ------------------------------------------------------------------ health


class ComponentHealth(BaseModel):
    ok: bool
    detail: str | None = None
    extra: dict[str, Any] | None = None


class HealthOut(BaseModel):
    status: HealthStatus
    version: str
    uptime_seconds: float
    components: dict[str, ComponentHealth]


class CacheStatsOut(BaseModel):
    available: bool
    url: str
    counters: dict[str, int] = Field(default_factory=dict)
    hit_rate: dict[str, float | None] = Field(default_factory=dict)
    keys: dict[str, int] = Field(default_factory=dict)
    ttl_seconds: dict[str, int] = Field(default_factory=dict)
    error: str | None = None
