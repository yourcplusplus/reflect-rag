#!/usr/bin/env python3
"""Compare ablation variants (V0-V4) from run_eval results.

Usage:
  python evals/compare.py                     # 取 runs/ 下每个 variant 的最新一次
  python evals/compare.py --pairs V0:V2 V2:V3 # 指定配对（默认 V0:V2 V2:V3）
"""
import argparse
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

from scipy import stats

RUNS_DIR = Path(__file__).resolve().parents[1] / "evals" / "results" / "runs"
NUMERIC = [("mrr", "MRR"), ("latency_ms", "Latency(ms)")]
BINARY = [("intent_match", "路由准确"), ("veto_free", "无幻觉(veto=0)"),
          ("refusal_correct", "拒答正确")]
PAIRWISE_DEFAULT = [("V0", "V2"), ("V2", "V3")]


def latest_results(runs_dir: Path, variant: str):
    d = runs_dir / variant
    if not d.is_dir():
        return None, None
    files = sorted(d.glob("*/results.json"))
    if not files:
        return None, None
    latest = files[-1]
    return json.loads(latest.read_text(encoding="utf-8")), latest


def ci95(values):
    """mean, half-width of the 95% CI (normal approximation)."""
    n = len(values)
    if n == 0:
        return None, None
    mean = statistics.mean(values)
    if n < 2:
        return mean, 0.0
    sd = statistics.stdev(values)
    half = 0.0 if sd == 0 else stats.norm.interval(0.95, loc=mean, scale=sd / n ** 0.5)[1] - mean
    return mean, max(0.0, half)


def mcnemar(a_pass: set, b_pass: set):
    """Exact McNemar (binomial) on paired binary outcomes."""
    only_a, only_b = len(a_pass - b_pass), len(b_pass - a_pass)
    n = only_a + only_b
    if n == 0:
        return {"only_a": only_a, "only_b": only_b, "p": None, "significant": False}
    p = stats.binomtest(min(only_a, only_b), n, 0.5).pvalue
    return {"only_a": only_a, "only_b": only_b, "p": round(p, 4), "significant": p < 0.05}


def collect(payload):
    """Per-item normalized records + binary outcome sets."""
    rows = {}
    for r in payload["results"]:
        veto_free = not r["veto_triggered"]
        refusal_ok = None
        if r["expected_behavior"] == "refusal":
            refusal_ok = bool(r["refusal_detected"] and veto_free)
        rows[r["id"]] = {**r, "veto_free": veto_free, "refusal_correct": refusal_ok,
                         "pass": r["intent_match"] and veto_free
                         and (refusal_ok if refusal_ok is not None else True)}
    binary = {
        "intent_match": {k for k, v in rows.items() if v["intent_match"]},
        "veto_free": {k for k, v in rows.items() if v["veto_free"]},
        "refusal_correct": {k for k, v in rows.items() if v["refusal_correct"]},
        "pass": {k for k, v in rows.items() if v["pass"]},
    }
    return rows, binary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-dir", default=str(RUNS_DIR))
    ap.add_argument("--pairs", nargs="*", default=[f"{a}:{b}" for a, b in PAIRWISE_DEFAULT])
    ap.add_argument("--out", default=None, help="markdown 报告输出路径")
    args = ap.parse_args()
    runs_dir = Path(args.runs_dir)

    variants = {}
    for d in sorted(runs_dir.glob("*/*/results.json")):
        payload = json.loads(d.read_text(encoding="utf-8"))
        v = payload.get("variant")
        # 旧版 summary 无 latency_ms 时从逐题 trace 回填（保持已跑数据可用）
        if "latency_ms" not in payload.get("summary", {}):
            by_layer, total = {}, 0
            for r in payload.get("results", []):
                total += r.get("latency_ms", 0)
                tp = r.get("trace_path")
                if not tp or not Path(tp).exists():
                    continue
                try:
                    bl = json.loads(Path(tp).read_text(encoding="utf-8")).get("summary", {}).get("latency_ms", {}).get("by_layer", {})
                except Exception:
                    bl = {}
                for layer, ms in bl.items():
                    by_layer[layer] = by_layer.get(layer, 0) + ms
            payload["summary"]["latency_ms"] = {"total": total, "by_layer": by_layer}
        if v and (v not in variants or d.parent.name > variants[v][1].parent.name):
            variants[v] = (payload, d)
    if not variants:
        print("runs/ 下没有 results.json")
        return 2

    lines = ["# V0-V4 消融对比报告", ""]
    for v, (payload, d) in sorted(variants.items()):
        p = payload.get("profile", {})
        lines.append(f"- **{v}**: {d.parent.name} | mode={p.get('retrieval_mode')} "
                     f"| reranker={p.get('reranker_enabled')} | critique={p.get('critique_enabled')} "
                     f"| n={payload['summary']['total']}")
    lines.append("")

    rows_by_variant = {v: collect(pl)[0] for v, (pl, _) in variants.items()}
    bin_by_variant = {v: collect(pl)[1] for v, (pl, _) in variants.items()}

    # --- 数值指标（均值 ± 95% CI，按 query_type 汇总行）---
    lines.append("## 数值指标（均值 [95% CI]）\n")
    for metric, label in NUMERIC:
        lines.append(f"### {label}\n")
        lines.append("| variant | ALL | single_paper_factual | cross_paper_comparison | cross_paper_multi_hop | term_ambiguity | unanswerable |")
        lines.append("|---|---|---|---|---|---|---|")
        for v, rows in sorted(rows_by_variant.items()):
            cells = []
            for scope in ("ALL", "single_paper_factual", "cross_paper_comparison",
                          "cross_paper_multi_hop", "term_ambiguity", "unanswerable"):
                vals = [r[metric] for rid, r in rows.items()
                        if r.get(metric) is not None
                        and (scope == "ALL" or r["query_type"] == scope)]
                mean, half = ci95(vals)
                cells.append(f"{mean:.3f} ±{half:.3f}" if mean is not None else "n/a")
            lines.append(f"| {v} | " + " | ".join(cells) + " |")
        lines.append("")

    # --- 二元指标（比例 ± 95% CI）---
    lines.append("## 二元指标（比例 [95% CI]）\n")
    for metric, label in BINARY:
        lines.append(f"### {label}\n")
        lines.append("| variant | ALL | single_paper_factual | cross_paper_comparison | cross_paper_multi_hop | term_ambiguity | unanswerable |")
        lines.append("|---|---|---|---|---|---|---|")
        for v, binary in sorted(bin_by_variant.items()):
            cells = []
            for scope in ("ALL", "single_paper_factual", "cross_paper_comparison",
                          "cross_paper_multi_hop", "term_ambiguity", "unanswerable"):
                if metric == "refusal_correct" and scope != "unanswerable":
                    cells.append("n/a")
                    continue
                ids = [rid for rid, r in rows.items()
                       if scope == "ALL" or r["query_type"] == scope]
                ids = [rid for rid in ids if rows[rid].get(metric) is not None]
                if not ids:
                    cells.append("n/a")
                    continue
                rate = len(binary[metric] & set(ids)) / len(ids)
                _, half = ci95([1.0 if rid in binary[metric] else 0.0 for rid in ids])
                cells.append(f"{rate * 100:.1f}% ±{half * 100:.1f}")
            lines.append(f"| {v} | " + " | ".join(cells) + " |")
        lines.append("")

    # --- 配对 McNemar ---
    lines.append("## 配对 McNemar 检验（二元指标）\n")
    pairs = [(a.split(":")[0], a.split(":")[1]) for a in args.pairs]
    for va, vb in pairs:
        if va not in bin_by_variant or vb not in bin_by_variant:
            continue
        lines.append(f"### {va} vs {vb}\n")
        lines.append("| 指标 | 仅A通过 | 仅B通过 | p | 显著性 |")
        lines.append("|---|---|---|---|---|")
        for metric, label in BINARY:
            m = mcnemar(bin_by_variant[va][metric], bin_by_variant[vb][metric])
            p = m["p"]
            sig = "—" if p is None else ("显著" if m["significant"] else "不显著")
            lines.append(f"| {label} | {m['only_a']} | {m['only_b']} | "
                         f"{'n/a' if p is None else p} | {sig} |")
        lines.append("")

    # --- 失败归因分布 ---
    lines.append("## 失败归因分布\n")
    lines.append("| variant | retrieval_miss | reranker_misrank | critique_miss | generation_hallucination |")
    lines.append("|---|---|---|---|---|")
    for v, (payload, _) in sorted(variants.items()):
        fa = payload["summary"].get("failure_attribution", {})
        lines.append(f"| {v} | {fa.get('retrieval_miss', 0)} | {fa.get('reranker_misrank', 0)} "
                     f"| {fa.get('critique_miss', 0)} | {fa.get('generation_hallucination', 0)} |")
    lines.append("")

    out = Path(args.out) if args.out else runs_dir / f"compare_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\n报告写入: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
