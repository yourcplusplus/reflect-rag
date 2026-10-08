#!/usr/bin/env python3
"""Post-hoc RAGAS metrics over a completed eval run.

Computes faithfulness / answer_correctness / context_precision / context_recall
per item from the answers and contexts recorded by run_eval.py. Unanswerable
items are skipped by default (their refusal correctness is already a metric).

Usage:
  python evals/ragas_backfill.py --run evals/results/runs/V3/<stamp> [--limit 10]
Resume: partial scores are appended to ragas_partial.jsonl in the same dir;
re-running skips completed ids and rewrites ragas_results.json.
"""
import argparse
import json
import math
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "project"))

from dotenv import load_dotenv
load_dotenv(ROOT / "project" / ".env")

import config
import yaml
from datasets import Dataset
from langchain_deepseek import ChatDeepSeek
from langchain_huggingface import HuggingFaceEmbeddings
from ragas import evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import answer_correctness, answer_relevancy, context_precision, context_recall, faithfulness

METRICS = [faithfulness, answer_correctness, context_precision, context_recall, answer_relevancy]
METRIC_NAMES = [m.name for m in METRICS]


def _answer_relevancy_local(raw_llm, raw_emb, question: str, answer: str, n: int = 3):
    """RAGAS-compatible answer_relevancy, implemented locally.

    Same algorithm as ragas' ResponseRelevancy (generate n questions from the
    response, mean cosine similarity to the original question, zeroed when the
    answer is noncommittal) — but ragas 0.4.3's PydanticPrompt path returns nan
    against OpenAI-compatible endpoints (question-generation parse failure), so
    we drive the generation through with_structured_output instead.
    """
    import numpy as np
    from langchain_core.messages import HumanMessage, SystemMessage
    from pydantic import BaseModel

    class ARQuestions(BaseModel):
        questions: list[str]
        noncommittal: int

    resp = raw_llm.with_structured_output(ARQuestions).invoke([
        SystemMessage(content=(
            f"Generate {n} different questions that the ANSWER below could be responding to. "
            "Then judge whether the answer is noncommittal (evasive, vague, or equivalent to "
            "'I don't know'): set noncommittal=1 if so, else 0.")),
        HumanMessage(content=f"ANSWER:\n{answer[:3000]}"),
    ])
    qs = [q.strip() for q in (resp.questions or []) if q and q.strip()][:n]
    if not qs:
        return None
    qv = np.asarray(raw_emb.embed_query(question))
    gv = np.asarray(raw_emb.embed_documents(qs))
    sim = (gv @ qv) / (np.linalg.norm(gv, axis=1) * np.linalg.norm(qv))
    return round(float(sim.mean()) * int(not resp.noncommittal), 4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=None, help="含 results.json 的 run 目录")
    ap.add_argument("--results", default=None, help="results.json 文件路径（代替 --run）")
    ap.add_argument("--limit", type=int, default=None, help="只算前 N 条（试跑用）")
    ap.add_argument("--include-unanswerable", action="store_true")
    ap.add_argument("--summary-only", action="store_true", help="跳过计算，仅从 partial 重新汇总")
    ap.add_argument("--dataset", default=str(ROOT / "evals" / "golden_dataset.yaml"),
                    help="按 id 联结 ground_truth 的数据集（run_eval 未在 results 里记录 GT）")
    ap.add_argument("--metrics", default=None,
                    help="逗号分隔的指标子集（faithfulness,answer_correctness,context_precision,context_recall）")
    args = ap.parse_args()

    if not args.run and not args.results:
        print("ERROR: 需要 --run <目录> 或 --results <results.json 路径>")
        return 2
    if args.results:
        results_path = Path(args.results)
        run_dir = results_path.parent
    else:
        run_dir = Path(args.run)
        results_path = run_dir / "results.json"
    payload = json.loads(results_path.read_text(encoding="utf-8"))
    ds = yaml.safe_load(Path(args.dataset).read_text(encoding="utf-8"))
    gt_by_id = {it["id"]: it.get("ground_truth", "") for it in ds["items"]}
    items = [r for r in payload["results"] if r["outcome"] == "ok"]
    if not args.include_unanswerable:
        items = [r for r in items if r["expected_behavior"] == "answer"]
    if args.limit:
        items = items[:args.limit]

    metrics = METRICS
    if args.metrics:
        wanted = {m.strip() for m in args.metrics.split(",")}
        metrics = [m for m in METRICS if m.name in wanted]
        assert metrics, f"未知指标集: {args.metrics}（可选: {[m.name for m in METRICS]}）"

    ragas_partial = run_dir / "ragas_partial.jsonl"
    done = {}
    if ragas_partial.exists():
        for line in ragas_partial.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                done[rec["id"]] = rec
        print(f"[resume] 载入 {len(done)} 条已完成评分", flush=True)
    def _is_missing(v):
        if v is None:
            return True
        try:
            return math.isnan(float(v))
        except (TypeError, ValueError):
            return True

    def _missing_metrics(rec_id):
        rec = done.get(rec_id, {})
        return [m for m in metrics if _is_missing(rec.get(m.name))]

    todo = [(r, ms) for r in items if (ms := _missing_metrics(r["id"]))]
    if args.summary_only:
        todo = []
    total_metric_calls = sum(len(ms) for _, ms in todo)
    print(f"[ragas] 待算 {len(todo)}/{len(items)} 条（缺失指标共 {total_metric_calls} 个）| 模型={config.LLM_MODEL}", flush=True)

    if todo:
        raw_llm = ChatDeepSeek(
            model=config.LLM_MODEL,
            api_key=config.DEEPSEEK_API_KEY,
            api_base=config.DEEPSEEK_BASE_URL,
            temperature=0, request_timeout=120)
        raw_emb = HuggingFaceEmbeddings(model_name=config.DENSE_MODEL)
        llm = LangchainLLMWrapper(raw_llm)
        emb = LangchainEmbeddingsWrapper(raw_emb)

        for i, (r, missing) in enumerate(todo, 1):
            gt = gt_by_id.get(r["id"])
            if not gt:
                print(f"[{i}/{len(todo)}] {r['id']} 数据集无对应 ground_truth，跳过", flush=True)
                continue
            row = {"question": r["question"], "answer": r["answer"],
                   "contexts": r.get("contexts", []), "ground_truth": gt}
            scores = dict(done.get(r["id"], {"id": r["id"], "query_type": r["query_type"]}))
            for metric in missing:
                if metric.name == "answer_relevancy":
                    try:
                        val = _answer_relevancy_local(raw_llm, raw_emb, r["question"], r["answer"])
                        if val is not None:
                            scores["answer_relevancy"] = val
                            scores.pop("answer_relevancy_error", None)
                        else:
                            scores["answer_relevancy"] = None
                            scores["answer_relevancy_error"] = "empty question generation"
                    except Exception as e:
                        scores["answer_relevancy"] = None
                        scores["answer_relevancy_error"] = str(e)[:300]
                    continue
                try:
                    res = evaluate(Dataset.from_dict({k: [v] for k, v in row.items()}),
                                   metrics=[metric], llm=llm, embeddings=emb)
                    # ragas 0.4.x 的 res[metric] 可能是 per-sample 列表；统一取标量
                    val = res[metric.name]
                    if isinstance(val, list):
                        val = val[0] if val else None
                    elif hasattr(val, "iloc"):
                        val = val.iloc[0]
                    if val is not None:
                        scores[metric.name] = round(float(val), 4)
                        scores.pop(metric.name + "_error", None)   # 清理历史错误
                    else:
                        scores[metric.name] = None
                except Exception as e:
                    scores[metric.name] = None
                    scores[metric.name + "_error"] = str(e)[:300]
            with open(ragas_partial, "a", encoding="utf-8") as f:
                f.write(json.dumps(scores, ensure_ascii=False) + "\n")
            done[r["id"]] = scores
            pretty = " ".join(f"{m.name}={scores.get(m.name)}" for m in missing)
            print(f"[{i}/{len(todo)}] {r['id']} {pretty}", flush=True)
            time.sleep(0.3)

    per_item = list(done.values())

    def _valid(v):
        if v is None:
            return False
        try:
            return not math.isnan(float(v))
        except (TypeError, ValueError):
            return True

    summary = {}
    for name in METRIC_NAMES:
        vals = [s[name] for s in per_item if _valid(s.get(name))]
        summary[name] = round(statistics.mean(vals), 4) if vals else None
    out = run_dir / "ragas_results.json"
    out.write_text(json.dumps({"summary": summary, "count": len(per_item),
                               "per_item": per_item}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"[done] {out}")
    print(f"[done] summary: {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
