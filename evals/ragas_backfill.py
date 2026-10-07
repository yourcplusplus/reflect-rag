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
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "project"))

from dotenv import load_dotenv
load_dotenv(ROOT / "project" / ".env")

import config
from datasets import Dataset
from langchain_deepseek import ChatDeepSeek
from langchain_huggingface import HuggingFaceEmbeddings
from ragas import evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import answer_correctness, context_precision, context_recall, faithfulness

METRICS = [faithfulness, answer_correctness, context_precision, context_recall]
METRIC_NAMES = [m.name for m in METRICS]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="含 results.json 的 run 目录")
    ap.add_argument("--limit", type=int, default=None, help="只算前 N 条（试跑用）")
    ap.add_argument("--include-unanswerable", action="store_true")
    args = ap.parse_args()

    run_dir = Path(args.run)
    payload = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
    items = [r for r in payload["results"] if r["outcome"] == "ok"]
    if not args.include_unanswerable:
        items = [r for r in items if r["expected_behavior"] == "answer"]
    if args.limit:
        items = items[:args.limit]

    ragas_partial = run_dir / "ragas_partial.jsonl"
    done = {}
    if ragas_partial.exists():
        for line in ragas_partial.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                done[rec["id"]] = rec
        print(f"[resume] 载入 {len(done)} 条已完成评分", flush=True)
    todo = [r for r in items if r["id"] not in done]
    print(f"[ragas] 待算 {len(todo)}/{len(items)} 条 | 模型={config.LLM_MODEL}", flush=True)

    if todo:
        llm = LangchainLLMWrapper(ChatDeepSeek(
            model=config.LLM_MODEL,
            api_key=config.DEEPSEEK_API_KEY,
            api_base=config.DEEPSEEK_BASE_URL,
            temperature=0, request_timeout=120))
        emb = LangchainEmbeddingsWrapper(HuggingFaceEmbeddings(model_name=config.DENSE_MODEL))

        for i, r in enumerate(todo, 1):
            row = {"question": r["question"], "answer": r["answer"],
                   "contexts": r.get("contexts", []), "ground_truth": r["ground_truth"]}
            scores = {"id": r["id"], "query_type": r["query_type"]}
            for metric in METRICS:
                try:
                    res = evaluate(Dataset.from_dict({k: [v] for k, v in row.items()}),
                                   metrics=[metric], llm=llm, embeddings=emb)
                    scores[metric.name] = round(float(res[metric.name]), 4)
                except Exception as e:
                    scores[metric.name] = None
                    scores[metric.name + "_error"] = str(e)[:150]
            with open(ragas_partial, "a", encoding="utf-8") as f:
                f.write(json.dumps(scores, ensure_ascii=False) + "\n")
            done[r["id"]] = scores
            pretty = " ".join(f"{m.name}={scores.get(m.name)}" for m in METRICS)
            print(f"[{i}/{len(todo)}] {r['id']} {pretty}", flush=True)
            time.sleep(0.3)

    per_item = list(done.values())
    summary = {}
    for name in METRIC_NAMES:
        vals = [s[name] for s in per_item if s.get(name) is not None]
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
