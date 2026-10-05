"""Structured per-request trace collection.

One TraceCollector per chat turn. Nodes obtain it through the LangGraph
config (config["configurable"]["trace_collector"], injected by
RAGSystem.get_config()); the collector is None unless config.TRACE_ENABLED
is on, so every emit call site can stay unconditional.

A finalized trace is one JSON file under config.TRACE_DIR plus one index
line in index.jsonl. Tracing must never break the chat: all I/O is guarded.
"""
import json
import time
import uuid
from datetime import datetime
from pathlib import Path

import config

LAYER_BY_NODE = {
    "main.intent_router": "intent",
    "main.rewrite_query": "rewrite",
    "main.faq_answer": "generation",
    "main.aggregate_answers": "generation",
    "main.summarize_history": "overhead",
    "main.request_clarification": "overhead",
    "agent.orchestrator": "generation",
    "agent.fallback_response": "generation",
    "agent.compress_context": "compression",
    "agent.should_compress_context": "overhead",
    "agent.collect_answer": "overhead",
    "agent.critique": "critique",
}


def collector_from_config(runnable_config) -> "TraceCollector | None":
    """Pull the request's TraceCollector out of a LangGraph RunnableConfig."""
    if not isinstance(runnable_config, dict):
        return None
    return (runnable_config.get("configurable") or {}).get("trace_collector")


def build_profile() -> dict:
    """Snapshot of the ablation-relevant configuration (V0-V4 self-description)."""
    return {
        "retrieval_mode": config.DEFAULT_RETRIEVAL_MODE,
        "reranker_enabled": True,
        "reranker_model": config.RERANKER_MODEL,
        "intent_router_enabled": True,
        "critique_enabled": True,
        "llm_model": config.LLM_MODEL,
        "retrieval_k": config.DEFAULT_RETRIEVAL_K,
        "top_k_multiplier": config.RERANKER_TOP_K_MULTIPLIER,
        "score_threshold": config.RETRIEVAL_SCORE_THRESHOLD,
    }


class TraceCollector:
    def __init__(self, thread_id: str, question: str):
        self.t0 = time.perf_counter()
        self.trace_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
        self.thread_id = thread_id
        self.question = question
        self.events = []
        self.layer_ms = {}
        self.intent = None

    def emit(self, layer: str, event: str, data: dict | None = None) -> None:
        self.events.append({
            "t_ms": self._t_ms(),
            "layer": layer,
            "event": event,
            "data": data or {},
        })

    def intent_classified(self, intent: str, latency_ms: float) -> None:
        self.intent = intent
        self._add_layer("intent", latency_ms)
        self.emit("intent", "intent_classified", {"intent": intent, "latency_ms": round(latency_ms)})

    def node_exec(self, name: str, latency_ms: float, error: Exception | None = None) -> None:
        layer = LAYER_BY_NODE.get(name, "other")
        self._add_layer(layer, latency_ms)
        data = {"node": name, "latency_ms": round(latency_ms)}
        if error is not None:
            data["error"] = str(error)
        self.emit(layer, "node_error" if error else "node_exec", data)

    def _add_layer(self, layer: str, latency_ms: float) -> None:
        self.layer_ms[layer] = self.layer_ms.get(layer, 0) + latency_ms

    def _t_ms(self) -> int:
        return round((time.perf_counter() - self.t0) * 1000)

    def finalize(self, outcome: str = "ok", error: Exception | None = None):
        """Write trace_<trace_id>.json + one index.jsonl line. Never raises."""
        try:
            traces_dir = Path(config.TRACE_DIR)
            traces_dir.mkdir(parents=True, exist_ok=True)
            total = round((time.perf_counter() - self.t0) * 1000)
            payload = {
                "meta": {
                    "trace_id": self.trace_id,
                    "thread_id": self.thread_id,
                    "started_at": datetime.now().astimezone().isoformat(timespec="milliseconds"),
                    "question": self.question,
                    "profile": build_profile(),
                },
                "events": self.events,
                "summary": {
                    "intent": self.intent,
                    "outcome": outcome,
                    "error": str(error) if error else None,
                    "latency_ms": {
                        "total": total,
                        "by_layer": {k: round(v) for k, v in self.layer_ms.items()},
                    },
                },
            }
            out_path = traces_dir / f"trace_{self.trace_id}.json"
            out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
            with open(traces_dir / "index.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "trace_id": self.trace_id,
                    "question": self.question[:80],
                    "intent": self.intent,
                    "outcome": outcome,
                    "total_ms": total,
                    "file": out_path.name,
                }, ensure_ascii=False) + "\n")
            return out_path
        except Exception as exc:
            print(f"[trace] finalize failed (ignored): {exc}")
            return None


def start_trace(rag_system, question: str) -> "TraceCollector | None":
    """Create the per-turn collector and attach it to the rag system. Returns
    None when tracing is disabled (all node emit sites then see None)."""
    if not config.TRACE_ENABLED:
        rag_system.trace_collector = None
        return None
    collector = TraceCollector(thread_id=rag_system.thread_id, question=question)
    rag_system.trace_collector = collector
    return collector


def finish_trace(rag_system, outcome: str = "ok", error: Exception | None = None):
    collector = getattr(rag_system, "trace_collector", None)
    rag_system.trace_collector = None
    if collector is None:
        return None
    return collector.finalize(outcome=outcome, error=error)
