#!/usr/bin/env python3
"""Run the golden dataset through the RAG pipeline for ablation experiments.

Variants are selected via environment variables at process start:
  DEFAULT_RETRIEVAL_MODE=dense ENABLE_RERANKER=false ENABLE_CRITIQUE=false \
  TRACE_ENABLED=true python evals/run_eval.py --variant V0

Per item: invokes the graph with a fresh thread_id, collects intent, answer,
retrieval metrics (from the request trace), a hallucination veto gate, token
usage, and a failure attribution. Results land in
evals/results/runs/<variant>/<timestamp>/results.json
"""
import argparse
import json
import statistics
from collections import Counter, defaultdict
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "project"
sys.path.insert(0, str(PROJECT))

from dotenv import load_dotenv
load_dotenv(PROJECT / ".env")

import config
import yaml
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_deepseek import ChatDeepSeek
from pydantic import BaseModel
from core.rag_system import RAGSystem
from core.trace import start_trace, finish_trace, build_profile

RUNS_DIR = ROOT / "evals" / "results" / "runs"
REFUSAL_MARKERS = ["couldn't find", "no information", "not enough information",
                   " unable to", "未找到", "没有找到", "无法找到", "未能找到",
                   "没有相关信息", "不包含", "未收录", "没有收录"]


class TokenUsageHandler(BaseCallbackHandler):
    """Accumulate token usage across all LLM calls of one request."""

    def __init__(self):
        self.calls = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0

    def on_llm_end(self, response, **kwargs):
        self.calls += 1
        usage = (getattr(response, "llm_output", None) or {}).get("token_usage") or {}
        if not usage:
            for gen in (getattr(response, "generations", None) or []):
                for g in gen:
                    um = getattr(getattr(g, "message", None), "usage_metadata", None)
                    if um:
                        usage = {"prompt_tokens": um.get("input_tokens", 0),
                                 "completion_tokens": um.get("output_tokens", 0)}
        self.prompt_tokens += usage.get("prompt_tokens", 0) or 0
        self.completion_tokens += usage.get("completion_tokens", 0) or 0


def refusal_detected(answer: str) -> bool:
    low = answer.lower()
    return any(marker in low for marker in REFUSAL_MARKERS)


def extract_contexts(messages) -> list[str]:
    contexts = []
    for m in messages:
        if getattr(m, "type", "") != "tool":
            continue
        content = str(m.content)
        parts = (content.split(config.CHILD_CHUNK_SEPARATOR)
                 if getattr(m, "name", "") == "search_child_chunks" else [content])
        bad = ("NO_RELEVANT_CHUNKS", "NO_PARENT_DOCUMENT", "RETRIEVAL_ERROR:",
               "PARENT_RETRIEVAL_ERROR:", config.SKIPPED_TOOL_MESSAGE)
        contexts += [p.strip() for p in parts if p.strip() and not p.strip().startswith(bad)]
    return contexts


class VetoVerdict(BaseModel):
    fabricated: bool = False
    reason: str = ""


def veto_check(veto_llm, answer: str, contexts: list[str], expected_behavior: str):
    """Independent hallucination gate: are the answer's factual claims supported
    by the retrieved contexts? Unanswerable items must refuse instead."""
    if expected_behavior == "refusal":
        if refusal_detected(answer):
            return False, "correct refusal"
        return True, "unanswerable question was answered with substantive content"

    ctx_text = "\n\n".join(f"[{i}] {c[:800]}" for i, c in enumerate(contexts, 1)) or "(no contexts)"
    system = (
        "You are a hallucination auditor. For each factual claim in the ANSWER, "
        "check whether it is supported by the CONTEXTS. fabricated=true if ANY "
        "factual claim lacks support in the contexts. If the answer only states "
        "that no relevant information was found, fabricated=false."
    )
    human = f"CONTEXTS:\n{ctx_text}\n\nANSWER:\n{answer}"
    last = None
    for _ in range(3):
        try:
            r = veto_llm.with_structured_output(VetoVerdict).invoke(
                [SystemMessage(content=system), HumanMessage(content=human)])
            return bool(r.fabricated), r.reason
        except Exception as e:
            last = e
            time.sleep(2)
    return False, f"veto judge unavailable: {last}"   # fail-open, never blocks the metric


def _norm_source(s: str) -> str:
    """索引元数据的 source 是 '2210.03629.pdf'，数据集是 '2210.03629'——归一化后匹配。"""
    return str(s).strip().removesuffix(".pdf").removesuffix(".md").lower()


def retrieval_metrics(trace_payload: dict, source_papers: set) -> dict:
    source_papers = {_norm_source(s) for s in source_papers}
    rounds, pre_posts, point_source = [], [], {}
    for e in trace_payload.get("events", []):
        if e["event"] == "candidates":
            srcs = [_norm_source(c.get("source", "")) for c in e["data"].get("candidates", [])]
            rounds.append([i + 1 for i, s in enumerate(srcs) if s in source_papers])
            for c in e["data"].get("candidates", []):
                point_source[c["point_id"]] = _norm_source(c.get("source", ""))
        elif e["event"] == "reranked":
            pre_posts.append((e["data"].get("pre_rank", []), e["data"].get("post_rank", [])))

    best_rank = min((r for rnd in rounds for r in rnd), default=None)
    mrr = round(1.0 / best_rank, 4) if best_rank else 0.0
    recall_candidates = int(bool(rounds and any(any(rnd) for rnd in rounds)))
    recall_final = int(bool(rounds and any(r <= config.DEFAULT_RETRIEVAL_K for r in rounds[-1])))

    gold_pre, gold_post = [], []
    for pre, post in pre_posts:
        gold_pre += [i + 1 for i, pid in enumerate(pre) if _norm_source(point_source.get(pid, "")) in source_papers]
        gold_post += [i + 1 for i, pid in enumerate(post) if _norm_source(point_source.get(pid, "")) in source_papers]
    rerank_gain = (round(statistics.mean(gold_pre) - statistics.mean(gold_post), 3)
                   if gold_pre and gold_post else None)
    return {"mrr": mrr, "recall_candidates": recall_candidates, "recall_final": recall_final,
            "gold_rank_pre": gold_pre, "gold_rank_post": gold_post, "rerank_gain": rerank_gain}


def attribute_failure(res: dict, critique_enabled: bool) -> str | None:
    """First failing step in pipeline order. None = the item passed."""
    if res["intent_match"] is False and res["recall_candidates"] > 0:
        pass   # routing recorded separately; retrieval still evaluated
    if res["recall_candidates"] == 0:
        return "retrieval_miss"
    if res["recall_final"] == 0:
        return "reranker_misrank"
    if res["veto_triggered"]:
        if critique_enabled and res.get("critique_action") in ("accepted", "skipped_after_fallback"):
            return "critique_miss"
        return "generation_hallucination"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="V3")
    ap.add_argument("--dataset", default=str(ROOT / "evals" / "golden_dataset.yaml"))
    ap.add_argument("--limit", type=int, default=None, help="只跑前 N 条 approved（试跑用）")
    ap.add_argument("--query-type", default=None, help="只跑指定类目")
    ap.add_argument("--ragas", action="store_true", help="启用 RAGAS 指标（额外 token 成本）")
    ap.add_argument("--resume", default=None, help="续跑：指向已有的 run 目录（含 results_partial.jsonl）")
    args = ap.parse_args()

    data = yaml.safe_load(Path(args.dataset).read_text(encoding="utf-8"))
    items = [it for it in data["items"] if it.get("review_status") == "approved"]
    if args.query_type:
        items = [it for it in items if it["query_type"] == args.query_type]
    if args.limit:
        items = items[:args.limit]
    if not items:
        print("没有可运行的条目")
        return 2

    veto_llm = ChatDeepSeek(model=config.LLM_MODEL,
                            api_key=config.DEEPSEEK_API_KEY,
                            api_base=config.DEEPSEEK_BASE_URL,
                            temperature=0, request_timeout=60)

    try:
        rs = RAGSystem()
        rs.initialize()
    except RuntimeError as e:
        print(f"ERROR: {e}\n（Qdrant 被占用——先停掉正在运行的 app）")
        return 2

    if args.resume:
        out_dir = Path(args.resume)
        if not out_dir.is_dir():
            print(f"ERROR: resume 目录不存在: {out_dir}")
            return 2
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = RUNS_DIR / args.variant / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    partial_path = out_dir / "results_partial.jsonl"
    done: dict = {}
    if partial_path.exists():
        for line in partial_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                done[rec["id"]] = rec
        print(f"[resume] 载入 {len(done)} 条已完成记录", flush=True)
    pending = [it for it in items if it["id"] not in done]
    print(f"=== run {args.variant} | 待跑 {len(pending)}/{len(items)} | model={config.LLM_MODEL} "
          f"| mode={config.DEFAULT_RETRIEVAL_MODE} | reranker={config.ENABLE_RERANKER} "
          f"| critique={config.ENABLE_CRITIQUE} ===", flush=True)

    for i, it in enumerate(pending, 1):
        # 每题独立会话：共享 thread 会让上一题的澄清状态（pendingQuery/clarifications）
        # 污染下一题，导致连续澄清中断、全部跳过检索
        rs.thread_id = f"eval-{args.variant}-{it['id']}"
        collector = start_trace(rs, it["question"])
        cfg = rs.get_config()
        usage = TokenUsageHandler()
        cfg.setdefault("callbacks", [])
        cfg["callbacks"].append(usage)

        t0 = time.time()
        outcome, error = "ok", None
        tool_messages = []
        try:
            for _ns, chunk in rs.agent_graph.stream(
                    {"messages": [HumanMessage(content=it["question"])]},
                    config=cfg, stream_mode="updates", subgraphs=True):
                if not isinstance(chunk, dict):
                    continue
                for _node, update in chunk.items():
                    if _node == "__interrupt__" or not isinstance(update, dict):
                        continue
                    for m in update.get("messages", []):
                        if getattr(m, "type", "") == "tool":
                            tool_messages.append(m)
        except Exception as e:
            outcome, error = "error", e
        latency_ms = round((time.time() - t0) * 1000)
        trace_path = finish_trace(rs, outcome, error)

        state = rs.agent_graph.get_state(cfg)
        values = state.values or {}
        messages = values.get("messages", [])
        ai_msgs = [m for m in reversed(messages) if getattr(m, "type", "") == "ai" and str(m.content).strip()]
        answer = str(ai_msgs[0].content) if ai_msgs else ""
        intent = values.get("intent")

        contexts = extract_contexts(tool_messages)
        veto_triggered, veto_reason = veto_check(veto_llm, answer, contexts,
                                                 it.get("expected_behavior", "answer"))

        trace_payload = {}
        if trace_path:
            try:
                trace_payload = json.loads(Path(trace_path).read_text(encoding="utf-8"))
            except Exception:
                pass
        rmet = retrieval_metrics(trace_payload, set(it.get("source_papers", [])))

        intent_match = (intent == it.get("expected_intent"))
        refusal_ok = None
        if it.get("expected_behavior") == "refusal":
            refusal_ok = int(refusal_detected(answer) and not veto_triggered)

        crit_action = next((e["data"].get("action") for e in reversed(trace_payload.get("events", []))
                            if e["event"] == "verdict"), None)
        gate = {"recall_candidates": rmet["recall_candidates"], "recall_final": rmet["recall_final"],
                "intent_match": intent_match, "veto_triggered": veto_triggered}
        attribution = attribute_failure(gate, config.ENABLE_CRITIQUE)

        rec = {
            "id": it["id"], "question": it["question"], "query_type": it["query_type"],
            "expected_intent": it.get("expected_intent"), "intent": intent,
            "intent_match": intent_match,
            "expected_behavior": it.get("expected_behavior", "answer"),
            "answer": answer, "refusal_detected": refusal_detected(answer),
            "veto_triggered": veto_triggered, "veto_reason": veto_reason,
            "mrr": rmet["mrr"], "recall_candidates": rmet["recall_candidates"],
            "recall_final": rmet["recall_final"], "rerank_gain": rmet["rerank_gain"],
            "latency_ms": latency_ms,
            "latency_by_layer": (trace_payload.get("summary", {}).get("latency_ms", {}).get("by_layer")
                                 if trace_payload else {}),
            "token_usage": {"calls": usage.calls, "prompt_tokens": usage.prompt_tokens,
                            "completion_tokens": usage.completion_tokens},
            "critique_action": crit_action,
            "failure_attribution": attribution,
            "contexts": contexts,
            "trace_path": str(trace_path) if trace_path else None,
            "outcome": outcome, "error": str(error) if error else None,
        }
        with open(partial_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        done[it["id"]] = rec
        flags = (f"intent={'✓' if intent_match else '✗ ' + str(intent)}"
                 f" | veto={'✗' if veto_triggered else '—'}"
                 f" | MRR={rmet['mrr']}"
                 f" | 归因={attribution or '—'}"
                 f" | {latency_ms}ms | tokens={usage.prompt_tokens}+{usage.completion_tokens}")
        print(f"[{i}/{len(pending)}] {it['id']} {flags}", flush=True)

    results = [done[it["id"]] for it in items if it["id"] in done]

    passed = sum(1 for r in results if r["intent_match"] and not r["veto_triggered"]
                 and (r["refusal_detected"] if r["expected_behavior"] == "refusal" else True))
    layer_ms_total: dict = {}
    for r in results:
        for layer, ms in (r.get("latency_by_layer") or {}).items():
            layer_ms_total[layer] = layer_ms_total.get(layer, 0) + ms
    by_type = defaultdict(list)
    for r in results:
        by_type[r["query_type"]].append(r)
    payload = {
        "variant": args.variant,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "profile": build_profile(),
        "results": results,
        "summary": {
            "total": len(results), "passed": passed,
            "intent_acc": round(statistics.mean([r["intent_match"] for r in results]) * 100, 1) if results else 0,
            "veto_rate": round(statistics.mean([1 if r["veto_triggered"] else 0 for r in results]) * 100, 1) if results else 0,
            "mean_mrr": round(statistics.mean([r["mrr"] for r in results]), 3) if results else 0,
            "mean_latency_ms": round(statistics.mean([r["latency_ms"] for r in results])) if results else 0,
            "latency_ms": {"total": sum(r["latency_ms"] for r in results), "by_layer": {k: round(v) for k, v in layer_ms_total.items()}},
            "token_usage_total": {k: sum(r["token_usage"][k] for r in results)
                                  for k in ("calls", "prompt_tokens", "completion_tokens")},
            "failure_attribution": dict(Counter(r["failure_attribution"] for r in results
                                                if r["failure_attribution"])),
        },
    }
    payload["summary"]["by_query_type"] = {
        qt: {"n": len(rs_), "intent_acc": round(statistics.mean([r["intent_match"] for r in rs_]) * 100, 1),
             "mean_mrr": round(statistics.mean([r["mrr"] for r in rs_]), 3),
             "veto": sum(1 for r in rs_ if r["veto_triggered"])}
        for qt, rs_ in by_type.items()
    }
    (out_dir / "results.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"=== done: {passed}/{len(results)} passed | results.json → {out_dir / 'results.json'} ===", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
