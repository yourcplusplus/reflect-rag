#!/usr/bin/env python3
"""上下文池收敛收益复算（确定性、零 API 成本）——README "注入 token 下降 68%" 的出处脚本。

对两个 run 目录（收敛前 vs 收敛后，同题集）分别统计：
  - 每题最终注入的 contexts 条数（中位数 / 最大值 / 总和）
  - 注入总字符数与估算 token（chars/4，仅用于展示比例；结论以字符数为准）
  - 分题型的 contexts 中位数

Usage:
  python evals/context_pool_stats.py \
      --before evals/results/runs/V3-ctxA/20261009_204823 \
      --after  evals/results/runs/V3-conv/20261010_143849
"""
import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path


def stats_for(run_dir: Path) -> dict:
    results = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))["results"]
    counts = [len(r.get("contexts") or []) for r in results]
    chars = sum(len(c) for r in results for c in (r.get("contexts") or []))
    by_type: dict[str, list[int]] = defaultdict(list)
    for r in results:
        by_type[r["query_type"]].append(len(r.get("contexts") or []))
    return {
        "run": str(run_dir),
        "n_items": len(results),
        "ids": [r["id"] for r in results],
        "contexts_median": statistics.median(counts),
        "contexts_max": max(counts),
        "contexts_sum": sum(counts),
        "total_chars": chars,
        "est_tokens": chars // 4,
        "by_type_median": {qt: statistics.median(v) for qt, v in by_type.items()},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", required=True, help="收敛前的 run 目录")
    ap.add_argument("--after", required=True, help="收敛后的 run 目录")
    args = ap.parse_args()

    a, b = stats_for(Path(args.before)), stats_for(Path(args.after))
    if a["ids"] != b["ids"]:
        common = set(a["ids"]) & set(b["ids"])
        print(f"[warn] 题集不完全一致：交集 {len(common)} 题（before {a['n_items']} / after {b['n_items']}）")

    for s in (a, b):
        print(f"\n=== {s['run']} (n={s['n_items']}) ===")
        print(f"  contexts: 中位 {s['contexts_median']} | 最大 {s['contexts_max']} | 总和 {s['contexts_sum']}")
        print(f"  注入总字符: {s['total_chars']:,} | 估算 token(chars/4): {s['est_tokens']:,}")
        print(f"  分题型中位: {s['by_type_median']}")

    d_chars = (b["total_chars"] - a["total_chars"]) / a["total_chars"] * 100
    d_count = (b["contexts_sum"] - a["contexts_sum"]) / a["contexts_sum"] * 100
    print(f"\n=== 收敛收益（{a['run']} -> {b['run']}） ===")
    print(f"  注入字符: {a['total_chars']:,} -> {b['total_chars']:,}  ({d_chars:+.1f}%)")
    print(f"  contexts 总条数: {a['contexts_sum']} -> {b['contexts_sum']}  ({d_count:+.1f}%)")
    print(f"  contexts 中位: {a['contexts_median']} -> {b['contexts_median']}")
    print(f"  contexts 最大: {a['contexts_max']} -> {b['contexts_max']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
