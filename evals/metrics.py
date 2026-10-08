"""Retrieval-quality metrics shared by run_eval and offline backfill scripts.

nDCG is computed over the per-round candidate lists recorded in request
traces. Relevance is binary: a candidate is relevant when its source paper
appears in the item's gold source_papers.
"""
import math


def norm_source(s) -> str:
    """'2310.11511.pdf' -> '2310.11511' (与数据集 source_papers 对齐)."""
    return str(s).strip().removesuffix(".pdf").removesuffix(".md").lower()


def ndcg_at_k(candidates, gold_sources, k: int = 10):
    """Normalized DCG at k with binary relevance.

    candidates: retrieval result list, each entry a dict with a 'source' field
                (paper filename such as "2310.11511.pdf"), best rank first.
    gold_sources: gold paper ids from golden_dataset.yaml (e.g. ["2310.11511"]).

    DCG@k  = sum(rel_i / log2(i+1)) for i in 1..k   (i = rank, 1-based)
    IDCG@k = the same sum with all relevant documents placed first
    Returns DCG/IDCG, or 0.0 when IDCG is 0 (no relevant documents).
    """
    gold = {norm_source(g) for g in gold_sources}
    # 候选是 chunk 级、gold 是论文级：同一论文的多个 chunk 只保留最高排名位，
    # 否则 DCG 的相关条目数会超过 IDCG 的理想文档数，产出 >1 的 nDCG
    seen, deduped = set(), []
    for c in candidates:
        s = norm_source(c.get("source", ""))
        if s not in seen:
            seen.add(s)
            deduped.append(s)
    rels = [1 if s in gold else 0 for s in deduped[:k]]
    dcg = sum(rel / math.log2(i + 1) for i, rel in enumerate(rels, start=1))
    ideal_hits = min(len(gold), k)
    idcg = sum(1 / math.log2(i + 1) for i in range(1, ideal_hits + 1))
    if idcg == 0:
        return 0.0
    return dcg / idcg
