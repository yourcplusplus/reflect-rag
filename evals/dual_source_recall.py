#!/usr/bin/env python3
"""二源召回率复算（确定性、零 API 成本）——实验③。

针对多源题目（gold source_papers >= 2，即 cpc / cpm 类），从每个 run 的
results.json + request trace 复算：

  both_anywhere   所有 gold source 都出现在任一检索轮的候选里（召回上限）
  both_top5       所有 gold source 都曾在某轮候选的前 5 名出现过
  both_top10      同上，前 10 名
  final_contexts  所有 gold source 都留在最终注入的 contexts 里

为什么需要它：run_eval 的 recall_* 字段是"任一 gold 命中"（recall@1 源），
对多源题目恒为 1，掩盖了"cpc 只召回一半"的问题。本脚本补上全源口径。

Usage:
  python evals/dual_source_recall.py evals/results/runs/V0/20261007_112205 \
      evals/results/runs/V1/20261007_113831 [more runs...]
  # --dataset 指定金标集（默认 100 题全量集）
"""
import argparse
import json
import re
import statistics
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "evals" / "golden_dataset.yaml"

_FN_RE = re.compile(r"File Name:\s*(.+)")


def _norm_source(s: str) -> str:
    return str(s).strip().removesuffix(".pdf").removesuffix(".md").lower()


def gold_by_id(dataset_path: Path) -> dict[str, set[str]]:
    data = yaml.safe_load(dataset_path.read_text(encoding="utf-8"))
    return {
        it["id"]: {_norm_source(s) for s in it.get("source_papers", [])}
        for it in data["items"] if it.get("review_status") == "approved"
    }


def best_ranks_from_trace(trace_path: str) -> dict[str, int]:
    """gold source -> 历轮候选中的最好名次（1-based）。"""
    try:
        payload = json.loads(Path(trace_path).read_text(encoding="utf-8"))
    except Exception:
        return {}
    best: dict[str, int] = {}
    for e in payload.get("events", []):
        if e.get("event") != "candidates":
            continue
        for rank, c in enumerate(e["data"].get("candidates", []), start=1):
            src = _norm_source(c.get("source", ""))
            if src and (src not in best or rank < best[src]):
                best[src] = rank
    return best


def sources_in_contexts(contexts: list[str]) -> set[str]:
    found = set()
    for c in contexts:
        m = _FN_RE.search(c)
        if m:
            found.add(_norm_source(m.group(1)))
    return found


def evaluate_run(run_dir: Path, golds: dict[str, set[str]]) -> dict:
    results = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))["results"]
    rows = []
    for r in results:
        gold = golds.get(r["id"], set())
        if len(gold) < 2:
            continue  # 单源题（spf/term）不适用
        best = best_ranks_from_trace(r.get("trace_path") or "")
        in_ctx = sources_in_contexts(r.get("contexts") or [])
        rows.append({
            "id": r["id"],
            "query_type": r["query_type"],
            "n_gold": len(gold),
            "both_anywhere": int(all(g in best for g in gold)),
            "both_top10": int(all(best.get(g, 99) <= 10 for g in gold)),
            "both_top5": int(all(best.get(g, 99) <= 5 for g in gold)),
            "final_contexts": int(gold <= in_ctx),
            "partial_coverage": len(gold & (set(best) | in_ctx)) / len(gold),
        })
    def pct(key):
        return round(statistics.mean([row[key] for row in rows]) * 100, 1) if rows else None
    return {
        "run": str(run_dir),
        "n_multi_source": len(rows),
        "by_query_type": {
            qt: {"n": sum(1 for x in rows if x["query_type"] == qt),
                 "both_top5": round(statistics.mean(
                     [x["both_top5"] for x in rows if x["query_type"] == qt]) * 100, 1)}
            for qt in sorted({x["query_type"] for x in rows})
        },
        "both_anywhere_pct": pct("both_anywhere"),
        "both_top10_pct": pct("both_top10"),
        "both_top5_pct": pct("both_top5"),
        "final_contexts_pct": pct("final_contexts"),
        "mean_partial_coverage": round(statistics.mean([x["partial_coverage"] for x in rows]), 3) if rows else None,
        "rows": rows,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+", help="run 目录（含 results.json）")
    ap.add_argument("--dataset", default=str(DEFAULT_DATASET))
    ap.add_argument("--save", default=None, help="把明细存成 JSON 的路径")
    args = ap.parse_args()

    golds = gold_by_id(Path(args.dataset))
    out = []
    for run in args.runs:
        stats = evaluate_run(Path(run), golds)
        out.append(stats)
        print(f"\n=== {stats['run']} (多源题 n={stats['n_multi_source']}) ===")
        print(f"  双源均入候选(任意名次): {stats['both_anywhere_pct']}%")
        print(f"  双源均进 top10:        {stats['both_top10_pct']}%")
        print(f"  双源均进 top5:         {stats['both_top5_pct']}%")
        print(f"  双源均留最终 contexts: {stats['final_contexts_pct']}%")
        print(f"  平均部分覆盖率:        {stats['mean_partial_coverage']}")
        for qt, s in stats["by_query_type"].items():
            print(f"    [{qt}] n={s['n']} 双源均进 top5: {s['both_top5']}%")

    if args.save:
        Path(args.save).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n明细已保存: {args.save}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
