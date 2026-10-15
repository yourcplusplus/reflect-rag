"""The API's view of the RAG core.

One process-wide :class:`RagService` owns exactly one ``RAGSystem`` — the same
object graph the Gradio app builds in ``ui/gradio_app.py``: BGE-M3 dense
embeddings, the BM25 sparse encoder, the BGE reranker, the parent/child store
and the compiled LangGraph agent.

Two things the Gradio app does not need but the API does:

* **A thread lock.** ``RAGSystem`` keeps per-instance mutable state (``thread_id``,
  ``trace_collector``) and the underlying models are not safe to drive
  concurrently, so every chat turn and every indexing job runs under one lock.
  Requests that arrive while the lock is held are reported to the client as
  ``queued`` before they block.
* **A per-conversation thread.** ``RAGSystem.thread_id`` is the LangGraph
  checkpoint key; the API sets it to the conversation UUID so each conversation
  keeps its own agent memory instead of sharing one global thread.
"""
from __future__ import annotations

import asyncio
import logging
import threading
import time
from collections.abc import Callable, Iterator
from typing import Any

from api.settings import settings  # noqa: F401  (loads .env before the core imports below)

import config
from config import SKIPPED_TOOL_MESSAGE
from core.document_manager import DocumentManager
from core.rag_system import RAGSystem
from core.trace import finish_trace, start_trace
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, ToolMessage

logger = logging.getLogger("api.rag")

# Mirrors core/chat_interface.py: nodes whose partial output the client renders
# as a progress bubble, and the two nodes that emit the user-visible answer.
SYSTEM_NODES = {"summarize_history", "rewrite_query"}
FINAL_RESPONSE_NODES = {"aggregate_answers", "faq_answer"}


def _final_answer_from_state(values: Any) -> str:
    """Last plain AI message of the finished turn.

    Needed for turns that do not stream tokens into the answer — a clarification
    request ends the turn at the ``request_clarification`` interrupt, and its
    text only exists in the graph state.
    """
    messages = (values or {}).get("messages") or []
    for message in reversed(messages):
        if isinstance(message, AIMessage) and not getattr(message, "tool_calls", None):
            text = str(message.content or "").strip()
            if text:
                return text
    return ""


class RagService:
    """Lifecycle + streaming for the shared ``RAGSystem``."""

    def __init__(self) -> None:
        self.rag_system: RAGSystem | None = None
        self.document_manager: DocumentManager | None = None
        self.init_error: str | None = None
        self.init_seconds: float | None = None
        self.last_error: str | None = None
        self.started_at = time.time()
        self._ready = threading.Event()
        # Serializes chat turns and document indexing against the shared models.
        self.lock = threading.Lock()

    # ------------------------------------------------------------- lifecycle

    def initialize(self) -> None:
        """Build the RAG system. Blocking and heavy: call it from a worker thread."""
        started = time.perf_counter()
        try:
            rag_system = RAGSystem()
            rag_system.initialize()
            self.rag_system = rag_system
            self.document_manager = DocumentManager(rag_system)
            logger.info("RAG system ready (collection=%s)", rag_system.collection_name)
        except Exception as exc:
            self.init_error = f"{type(exc).__name__}: {exc}"
            logger.exception("RAG initialization failed")
        finally:
            self.init_seconds = round(time.perf_counter() - started, 2)
            self._ready.set()

    def shutdown(self) -> None:
        rag_system = self.rag_system
        if rag_system is None:
            return
        try:
            rag_system.observability.flush()
        except Exception:
            pass

    def wait_ready(self, timeout: float) -> bool:
        return self._ready.wait(timeout=timeout)

    @property
    def ready(self) -> bool:
        return self._ready.is_set() and self.init_error is None

    @property
    def initializing(self) -> bool:
        return not self._ready.is_set()

    @property
    def busy(self) -> bool:
        """True while a chat turn or an indexing job holds the RAG lock."""
        return self.lock.locked()

    @property
    def collection_name(self) -> str | None:
        return getattr(self.rag_system, "collection_name", None)

    @property
    def cache_namespace(self) -> str:
        """Everything that changes what an answer looks like, besides the question.

        Cached answers are keyed on this namespace, so flipping an ablation
        switch (retrieval mode / reranker / critique) can never replay an answer
        produced by a different configuration.
        """
        return "|".join(
            [
                f"collection={self.collection_name or 'unknown'}",
                f"mode={config.DEFAULT_RETRIEVAL_MODE}",
                f"rerank={int(bool(config.ENABLE_RERANKER))}",
                f"critique={int(bool(config.ENABLE_CRITIQUE))}",
                f"llm={config.LLM_MODEL}",
            ]
        )

    def status(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "initializing": self.initializing,
            "error": self.init_error,
            "init_seconds": self.init_seconds,
            "collection": self.collection_name,
            "cache_namespace": self.cache_namespace,
            "busy": self.busy,
            "uptime_seconds": round(time.time() - self.started_at, 1),
        }

    # ------------------------------------------------------------------ chat

    def stream_answer(self, question: str, *, thread_id: str | None = None) -> Iterator[dict[str, Any]]:
        """Run one chat turn, yielding structured events.

        Blocking generator: drive it from a worker thread (see
        :func:`iter_blocking`) so the event loop stays free. Event types:

        ``node`` (progress buffer of a system node), ``tool_call``,
        ``tool_result``, ``tool_skipped``, ``token`` (answer text delta),
        ``error``, ``final`` (answer + intent, always last).
        """
        rag_system = self.rag_system
        if rag_system is None or rag_system.agent_graph is None:
            yield {"type": "error", "detail": self.init_error or "RAG system is not initialized"}
            yield {"type": "final", "answer": "", "intent": None, "outcome": "error"}
            return

        with self.lock:
            if thread_id:
                # Each conversation gets its own LangGraph checkpoint thread.
                rag_system.thread_id = str(thread_id)
            question = question.strip()
            start_trace(rag_system, question)
            outcome: str = "ok"
            error: Exception | None = None
            answer_parts: list[str] = []
            answer = ""
            intent: str | None = None
            try:
                cfg = rag_system.get_config()
                current_state = rag_system.agent_graph.get_state(cfg)
                if current_state.next:
                    # The previous turn stopped at the clarification interrupt:
                    # append the new message and resume instead of restarting.
                    rag_system.agent_graph.update_state(
                        cfg, {"messages": [HumanMessage(content=question)]}
                    )
                    stream_input: dict[str, Any] | None = None
                else:
                    stream_input = {"messages": [HumanMessage(content=question)]}

                active_tool_calls: dict[str, str] = {}
                system_buffers: dict[str, str] = {}

                for chunk, metadata in rag_system.agent_graph.stream(
                    stream_input, config=cfg, stream_mode="messages"
                ):
                    node = metadata.get("langgraph_node", "")

                    if node in SYSTEM_NODES and isinstance(chunk, AIMessageChunk) and chunk.content:
                        buffer = system_buffers.get(node, "") + str(chunk.content)
                        system_buffers[node] = buffer
                        yield {"type": "node", "node": node, "text": buffer}

                    elif hasattr(chunk, "tool_calls") and chunk.tool_calls:
                        for tool_call in chunk.tool_calls:
                            call_id = tool_call.get("id")
                            if call_id and call_id not in active_tool_calls:
                                active_tool_calls[call_id] = tool_call.get("name", "")
                                yield {
                                    "type": "tool_call",
                                    "id": call_id,
                                    "name": tool_call.get("name", ""),
                                    "args": tool_call.get("args") or {},
                                }

                    elif isinstance(chunk, ToolMessage):
                        if str(chunk.content).startswith(SKIPPED_TOOL_MESSAGE):
                            name = active_tool_calls.pop(chunk.tool_call_id, "")
                            yield {"type": "tool_skipped", "id": chunk.tool_call_id, "name": name}
                        else:
                            yield {
                                "type": "tool_result",
                                "id": chunk.tool_call_id,
                                "name": active_tool_calls.get(chunk.tool_call_id) or str(getattr(chunk, "name", "") or ""),
                                "content": str(chunk.content),
                            }

                    elif isinstance(chunk, AIMessageChunk) and chunk.content and node in FINAL_RESPONSE_NODES:
                        text = str(chunk.content)
                        answer_parts.append(text)
                        yield {"type": "token", "text": text}

                final_state = rag_system.agent_graph.get_state(cfg)
                values = getattr(final_state, "values", None) or {}
                intent = values.get("intent") or intent
                answer = "".join(answer_parts).strip() or _final_answer_from_state(values)

            except GeneratorExit:  # client went away: release the lock, keep the trace honest
                outcome = "cancelled"
                raise
            except Exception as exc:
                outcome, error = "error", exc
                self.last_error = f"{type(exc).__name__}: {exc}"
                logger.exception("chat turn failed")
                if rag_system.trace_collector is not None:
                    try:
                        rag_system.trace_collector.emit("error", "chat_error", {"error": str(exc)})
                    except Exception:
                        pass
                yield {"type": "error", "detail": str(exc)}
            finally:
                try:
                    finish_trace(rag_system, outcome, error)
                except Exception:
                    pass

            yield {"type": "final", "answer": answer, "intent": intent, "outcome": outcome}

    # ------------------------------------------------------------- documents

    def index_documents(self, paths: list[str], progress_callback: Callable | None = None) -> tuple[int, int]:
        """Index PDFs/Markdown through the core ``DocumentManager`` (blocking)."""
        if self.document_manager is None:
            raise RuntimeError(self.init_error or "RAG system is not initialized")
        with self.lock:
            return self.document_manager.add_documents(paths, progress_callback=progress_callback)

    def list_sources(self) -> list[str]:
        if self.document_manager is None:
            return []
        try:
            return list(self.document_manager.get_markdown_files())
        except Exception as exc:
            logger.warning("Could not list knowledge-base sources: %s", exc)
            return []


async def iter_blocking(factory: Callable[[], Iterator[dict[str, Any]]], cancelled: threading.Event) -> Any:
    """Bridge a blocking generator into the event loop without blocking it.

    ``factory`` is called in a worker thread; items are handed back through an
    asyncio queue. When the client disconnects, ``cancelled`` is set and the
    generator is closed explicitly, which releases the RAG lock deterministically
    instead of waiting for garbage collection.
    """
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()
    _end = object()

    def put(value: Any) -> None:
        try:
            loop.call_soon_threadsafe(queue.put_nowait, value)
        except RuntimeError:
            pass  # loop already closed (server shutting down)

    def run() -> None:
        generator = factory()
        try:
            for item in generator:
                if cancelled.is_set():
                    break
                put(item)
        except Exception as exc:  # defensive: stream_answer already catches its own errors
            put({"type": "error", "detail": f"{type(exc).__name__}: {exc}"})
        finally:
            try:
                generator.close()
            except Exception:
                pass
            put(_end)

    thread = threading.Thread(target=run, name="rag-stream", daemon=True)
    thread.start()
    try:
        while True:
            item = await queue.get()
            if item is _end:
                break
            yield item
    finally:
        cancelled.set()
