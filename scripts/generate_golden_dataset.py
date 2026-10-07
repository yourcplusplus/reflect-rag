#!/usr/bin/env python3
"""Generate the golden dataset draft (100 items) from markdown_docs/.

Pipeline: inventory → embed → generate (5 categories) → verify → assemble.

Outputs:
  evals/golden_dataset.yaml                    — the draft dataset (100 items, review_status: pending)
  evals/results/generation/items.jsonl         — raw per-item records (resume + audit)
  evals/results/generation/review_draft.md     — human-friendly review listing

Resume: re-running skips categories/papers already recorded in items.jsonl.
Usage:
  python scripts/generate_golden_dataset.py --limit 2        # gate run (2 items/category)
  python scripts/generate_golden_dataset.py                  # full 100-item draft
  python scripts/generate_golden_dataset.py --no-verify      # skip the LLM judge pass
"""
import argparse
import json
import re
import sys
import time
import uuid
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "project"
sys.path.insert(0, str(PROJECT))

from dotenv import load_dotenv
load_dotenv(PROJECT / ".env")

import config
import yaml
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_deepseek import ChatDeepSeek
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field

GEN_DIR = ROOT / "evals" / "results" / "generation"
ITEMS_JSONL = GEN_DIR / "items.jsonl"
OUT_YAML = ROOT / "evals" / "golden_dataset.yaml"
REVIEW_MD = GEN_DIR / "review_draft.md"

STOPWORDS = {
    "the", "of", "and", "to", "in", "is", "for", "we", "our", "a", "an", "are", "was", "were",
    "be", "been", "has", "have", "had", "on", "at", "as", "by", "that", "this", "these", "those",
    "with", "from", "which", "where", "using", "based", "paper", "papers", "method", "methods",
    "model", "models", "results", "result", "table", "figure", "section", "propose", "proposed",
    "approach", "approaches", "also", "can", "more", "than", "then", "when", "what", "how",
    "into", "over", "such", "not", "each", "between", "during", "through", "their", "its",
    "them", "they", "number", "page", "pages", "time", "data", "information", "system",
    "systems", "training", "knowledge", "question", "questions", "answer", "answers", "text",
    "language", "large", "performance", "evaluation", "task", "tasks", "source", "sources",
    "document", "documents", "content", "different", "high", "low", "new", "first", "second",
    "third", "one", "two", "three", "four", "five", "test", "tests", "work", "works", "study",
    "studies", "used", "introduced", "demonstrate", "demonstrated", "show", "showed", "shown",
    "present", "presented", "achieve", "achieved", "improve", "improved", "outperform",
    "outperforms", "retrieval", "generation", "augmented", "accuracy", "benchmark",
    "benchmarks", "experiment", "experiments", "dataset", "datasets", "corpus", "context",
    "contexts", "passage", "passages", "query", "queries", "relevant", "relevance", "quality",
    "technique", "techniques", "effectiveness", "framework", "frameworks", "process", "step",
    "while", "start", "https", "http", "end", "case", "cases", "use", "way", "ways", "part",
    "key", "main", "best", "common", "single", "multiple", "general", "specific", "simple",
    "complex", "real", "true", "false", "given", "following", "various", "several", "current",
    "recent", "existing", "original", "final", "overall", "additional", "available",
    "important", "possible", "able", "small", "long", "short", "old", "early", "late",
    "future", "past", "idea", "ideas", "example", "examples", "type", "types", "level",
    "levels", "point", "points", "term", "terms", "value", "values", "size", "sizes",
}

CATEGORY_TARGETS = {
    "single_paper_factual": 25,
    "cross_paper_comparison": 25,
    "cross_paper_multi_hop": 25,
    "term_ambiguity": 10,
    "unanswerable": 15,
}
ID_PREFIX = {
    "single_paper_factual": "spf",
    "cross_paper_comparison": "cpc",
    "cross_paper_multi_hop": "cpm",
    "term_ambiguity": "tam",
    "unanswerable": "una",
}
# 已知锚点配对（同主题族，优先纳入对比/多跳）
ANCHOR_PAIRS = [
    ("2210.03629", "2310.11511"),   # ReAct / Self-RAG
    ("2310.11511", "2401.15884"),   # Self-RAG / CRAG
    ("2401.18059", "2404.16130"),   # RAPTOR / GraphRAG
    ("2005.11401", "2210.03629"),   # RAG / ReAct
]


# ---------- Pydantic schemas for structured generation ----------

class SinglePaperQ(BaseModel):
    """One factual question answerable ONLY from the given passage."""
    question: str = Field(description="问题（与原文同语言）")
    ground_truth: str = Field(description="标准答案，2-4 句，只用给定原文")
    gold_evidence: str = Field(description="支撑答案的原文句子，逐字摘录")
    expected_intent: str = Field(description="simple_faq（概念定义）或 single_hop（具体事实查询）")


class ComparisonQ(BaseModel):
    question: str = Field(description="对比型问题，必须同时依赖 A 和 B")
    ground_truth: str = Field(description="综合两篇的标准答案，3-6 句")
    evidence_a: str = Field(description="论文 A 中支撑答案的原文摘录")
    evidence_b: str = Field(description="论文 B 中支撑答案的原文摘录")


class MultiHopQ(BaseModel):
    question: str = Field(description="多跳问题：必须先理解 A 的结论才能理解/评价 B")
    ground_truth: str = Field(description="跨论文综合答案，3-6 句")
    evidence_a: str = Field(description="论文 A 中的关键原文摘录")
    evidence_b: str = Field(description="论文 B 中的关键原文摘录")
    reasoning_bridge: str = Field(description="A→B 的推理桥接说明")


class TermQ(BaseModel):
    term: str = Field(description="存在跨论文含义分歧的术语")
    question: str = Field(description="关于该术语在不同论文中含义差异的问题")
    ground_truth: str = Field(description="分论文说明各自含义，并指出分歧")
    meanings: list[str] = Field(description="各论文中该术语的含义，格式 'paper_id: 含义'")


class UnanswerableList(BaseModel):
    questions: list[str] = Field(description="知识库无法回答的问题列表")


class VerifyVerdict(BaseModel):
    supported: bool = Field(description="gold_evidence 是否足以支撑 ground_truth")
    reason: str = Field(description="判定理由，一句话")


# ---------- LLM helpers ----------

def make_llm():
    if not config.DEEPSEEK_API_KEY:
        print("ERROR: DEEPSEEK_API_KEY is not set (project/.env)")
        sys.exit(2)
    return ChatDeepSeek(
        model=config.LLM_MODEL,
        api_key=config.DEEPSEEK_API_KEY,
        api_base=config.DEEPSEEK_BASE_URL,
        temperature=0.3,
        request_timeout=90,
    )


def gen_call(llm, schema, system: str, human: str, retries: int = 3):
    """Structured-output call with retry. Raises after the last failure."""
    last = None
    for attempt in range(1, retries + 1):
        try:
            return llm.with_structured_output(schema).invoke(
                [SystemMessage(content=system), HumanMessage(content=human)]
            )
        except Exception as e:
            last = e
            wait = 2 ** attempt
            print(f"    [retry {attempt}/{retries}] {type(e).__name__}: {e} (wait {wait}s)", flush=True)
            time.sleep(wait)
    raise last


# ---------- Phase 1: inventory ----------

def load_inventory():
    """paper_id → title + passages (section-anchored)."""
    header_splitter = MarkdownHeaderTextSplitter(config.HEADERS_TO_SPLIT_ON, strip_headers=False)
    sub_splitter = RecursiveCharacterTextSplitter(chunk_size=1400, chunk_overlap=100)
    papers = []
    for md in sorted((ROOT / "markdown_docs").glob("*.md")):
        paper_id = md.stem
        text = md.read_text(encoding="utf-8")
        h1_lines = [ln[2:].strip(" *") for ln in text.splitlines() if ln.startswith("# ")]
        non_abstract = [t2 for t2 in h1_lines if t2 and t2.lower() not in {"abstract", "summary", "abst"}]
        title = non_abstract[0] if non_abstract else (h1_lines[0] if h1_lines else paper_id)
        docs = header_splitter.split_text(text)
        passages = []
        for d in docs:
            chain = " > ".join(v for k, v in d.metadata.items() if k.startswith("Header") and v)
            section = chain or "(front matter)"
            for piece in sub_splitter.split_text(d.page_content):
                passages.append({"paper": paper_id, "section": section, "text": piece})
        if not passages:
            passages = [{"paper": paper_id, "section": "(no headers)", "text": text[:1400]}]
        papers.append({"paper": paper_id, "title": title, "passages": passages})
    return papers


def pick_passages(paper, keywords, n):
    """Prefer passages matching keywords (abstract/intro/conclusion), else first n."""
    scored = []
    for i, p in enumerate(paper["passages"][:80]):
        score = sum(1 for kw in keywords if kw in p["text"].lower()) * 10 - i * 0.1
        scored.append((score, i, p))
    scored.sort(reverse=True)
    return [p for _, _, p in scored[:n]]


# ---------- Phase 2: embeddings ----------

_EMBED = None
def get_embed():
    global _EMBED
    if _EMBED is None:
        print("[embed] loading embeddings model...", flush=True)
        _EMBED = HuggingFaceEmbeddings(model_name=config.DENSE_MODEL)
    return _EMBED


def embed_texts(texts, batch=32):
    emb = get_embed()
    out = []
    for i in range(0, len(texts), batch):
        out.extend(emb.embed_documents(texts[i:i + batch]))
        if (i // batch) % 10 == 0:
            print(f"[embed] {i + len(texts[i:i + batch])}/{len(texts)}", flush=True)
    return out


def cosine(a, b):
    na, nb = sum(x * x for x in a) ** 0.5, sum(x * x for x in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return sum(x * y for x, y in zip(a, b)) / (na * nb)


# ---------- Phase 3: category generators ----------

def gen_single_paper(llm, papers, target, done_keys):
    """One question per paper (round-robin), grounded in a picked passage."""
    out = []
    kw = ["abstract", "introduction", "conclusion", "contribution", "摘要", "引言", "结论", "贡献"]
    for paper in papers:
        if len(out) >= target:
            break
        key = ("single_paper_factual", paper["paper"])
        if key in done_keys:
            continue
        passages = pick_passages(paper, kw, 2)
        passage = passages[0]
        print(f"[spf] {paper['paper']} ({len(out) + 1}/{target})", flush=True)
        schema = SinglePaperQ
        system = (
            "You create ONE factual QA item for a RAG evaluation dataset. "
            "The question must be answerable ONLY from the given passage. "
            "ground_truth must use only the passage (2-4 sentences). "
            "gold_evidence must be a VERBATIM excerpt from the passage. "
            "expected_intent: 'simple_faq' if the question asks what a concept is; "
            "'single_hop' if it asks what a specific paper/document reports."
        )
        system_extra = "The question MUST name the specific paper(s) explicitly (arXiv ID or paper name, e.g., 'GraphRAG（2404.16130）' or 'DPR（2004.04906）'). NEVER use corpus-relative references such as 'this paper', 'both papers', or 'these papers' — a standalone reader must be able to tell which paper(s) the question targets."
        human = f"PAPER: {paper['title']} ({paper['paper']})\n\nPASSAGE:\n{passage['text'][:3500]}"
        try:
            r = gen_call(llm, schema, system + " " + system_extra, human)
        except Exception as e:
            print(f"    [skip] generation failed: {e}")
            continue
        out.append({
            "_key": list(key),
            "category": "single_paper_factual",
            "question": r.question,
            "ground_truth": r.ground_truth,
            "gold_evidence": [r.gold_evidence],
            "provenance": "extractive",
            "source_papers": [paper["paper"]],
            "source_sections": [f"{paper['paper']}#{passage['section'][:80]}"],
            "expected_intent": r.expected_intent if r.expected_intent in ("simple_faq", "single_hop") else "single_hop",
            "expected_behavior": "answer",
            "audit": {"section": passage["section"][:120]},
        })
        done_keys.add(key)
        time.sleep(0.5)
    return out


def gen_pair_questions(llm, papers, pairs, target, kind, done_keys):
    """Comparison or multi-hop questions over paper pairs."""
    by_id = {p["paper"]: p for p in papers}
    out = []
    for pa, pb in pairs:
        if len(out) >= target:
            break
        key = (kind, pa, pb)
        if key in done_keys or pa not in by_id or pb not in by_id:
            continue
        A, B = by_id[pa], by_id[pb]
        pa_pass = pick_passages(A, ["abstract", "introduction", "contribution", "摘要", "引言", "贡献"], 1)[0]
        pb_pass = pick_passages(B, ["abstract", "introduction", "contribution", "摘要", "引言", "贡献"], 1)[0]
        print(f"[{kind.split('_')[-1]}] {pa} × {pb} ({len(out) + 1}/{target})", flush=True)
        if kind == "cross_paper_comparison":
            schema = ComparisonQ
            system = (
                "You create ONE comparison QA item for a RAG evaluation dataset. "
                "The question must require contrasting the two papers (approach, mechanism, or findings). "
                "ground_truth must synthesize BOTH passages (3-6 sentences). "
                "evidence_a/evidence_b must be VERBATIM excerpts from the respective passages. "
                "The question MUST name BOTH papers (Paper A and Paper B) explicitly (arXiv ID or paper name, e.g., 'GraphRAG（2404.16130）' or 'DPR（2004.04906）'). NEVER use corpus-relative references such as 'this paper', 'both papers', or 'these papers' — a standalone reader must be able to tell which paper(s) the question targets."
            )
            human = (f"PAPER A: {A['title']} ({pa})\nPASSAGE A:\n{pa_pass['text'][:4000]}\n\n"
                     f"PAPER B: {B['title']} ({pb})\nPASSAGE B:\n{pb_pass['text'][:4000]}")
        else:
            schema = MultiHopQ
            system = (
                "You create ONE multi-hop QA item for a RAG evaluation dataset. "
                "The question must REQUIRE understanding paper A's conclusion/limitation in order to "
                "interpret or evaluate paper B (e.g., 'what problem did A leave open that B addresses?'). "
                "It must NOT be answerable from either passage alone. "
                "reasoning_bridge explains the A→B link in one sentence. "
                "The question MUST name BOTH papers (Paper A and Paper B) explicitly (arXiv ID or paper name, e.g., 'GraphRAG（2404.16130）' or 'DPR（2004.04906）'). NEVER use corpus-relative references such as 'this paper', 'both papers', or 'these papers' — a standalone reader must be able to tell which paper(s) the question targets."
            )
            human = (f"PAPER A: {A['title']} ({pa})\nPASSAGE A:\n{pa_pass['text'][:4000]}\n\n"
                     f"PAPER B: {B['title']} ({pb})\nPASSAGE B:\n{pb_pass['text'][:4000]}")
        try:
            r = gen_call(llm, schema, system, human)
        except Exception as e:
            print(f"    [skip] generation failed: {e}")
            continue
        evidence = [getattr(r, "evidence_a", ""), getattr(r, "evidence_b", "")]
        item = {
            "_key": list(key),
            "category": kind,
            "question": r.question,
            "ground_truth": r.ground_truth,
            "gold_evidence": [e for e in evidence if e],
            "provenance": "llm_synthesized",
            "source_papers": [pa, pb],
            "source_sections": [f"{pa}#{pa_pass['section'][:80]}", f"{pb}#{pb_pass['section'][:80]}"],
            "expected_intent": "multi_hop",
            "expected_behavior": "answer",
            "audit": {"sections": [pa_pass["section"][:80], pb_pass["section"][:80]]},
        }
        if kind == "cross_paper_multi_hop":
            item["audit"]["reasoning_bridge"] = getattr(r, "reasoning_bridge", "")
        out.append(item)
        done_keys.add(key)
        time.sleep(0.5)
    return out


def gen_term_ambiguity(llm, papers, passages_by_paper, target, done_keys):
    """Terms used with diverging meanings across ≥3 papers."""
    term_docs = defaultdict(list)
    pattern_counts = Counter()
    for p in papers:
        per_paper = defaultdict(list)
        for passage in p["passages"]:
            for tok in set(re.findall(r"[A-Za-z][A-Za-z\-]{3,}", passage["text"])):
                tok = tok.lower()
                if tok in STOPWORDS or len(tok) < 5 or len(tok) > 30:
                    continue  # 同上：普通词与超长短语不入候选
                pattern_counts[tok] += 1
                per_paper[tok].append(passage)
        for tok, psgs in per_paper.items():
            term_docs[tok].append((p["paper"], psgs))
    by_paper = [(tok, cnt) for tok, cnt in pattern_counts.most_common(80)
                if len(term_docs[tok]) >= 3]
    print(f"[tam] {len(by_paper)} candidate terms with ≥3-paper coverage", flush=True)

    out = []
    for term, _ in by_paper:
        if len(out) >= target:
            break
        key = ("term_ambiguity", term)
        if key in done_keys:
            continue
        contexts = term_docs[term][:3]
        context_text = "\n\n".join(
            f"PAPER {pid}:\n" + "\n".join(f"...{pp['text'][:600]}..." for pp in psgs[:2])
            for pid, psgs in contexts)
        print(f"[tam] term={term} ({len(out) + 1}/{target})", flush=True)
        system = (
            "You check whether a technical term is used with DIFFERENT meanings in different papers. "
            "If the meanings are essentially the same, you must say so. "
            "Only if there is a real divergence, create ONE QA item asking about the term's "
            "cross-paper meaning difference. ground_truth must state each paper's meaning "
            "(format 'paper_id: meaning') and the divergence. "
        "The question MUST name the papers involved explicitly (arXiv ID or paper name, e.g., 'GraphRAG（2404.16130）' or 'DPR（2004.04906）'). NEVER use corpus-relative references such as 'this paper', 'both papers', or 'these papers' — a standalone reader must be able to tell which paper(s) the question targets."
        )
        human = f"TERM: {term}\n\nCONTEXTS:\n{context_text}"
        try:
            r = gen_call(llm, TermQ, system, human)
        except Exception as e:
            print(f"    [skip] {e}")
            continue
        papers_involved = [m.split(":")[0].strip() for m in r.meanings if ":" in m]
        if len(papers_involved) < 2:
            continue
        out.append({
            "_key": list(key),
            "category": "term_ambiguity",
            "question": r.question,
            "ground_truth": r.ground_truth,
            "gold_evidence": [m for m in r.meanings],
            "provenance": "extractive",
            "source_papers": papers_involved,
            "source_sections": [f"{pid}#term:{term}" for pid in papers_involved],
            "expected_intent": "multi_hop",
            "expected_behavior": "answer",
            "audit": {"term": r.term},
        })
        done_keys.add(key)
        time.sleep(0.5)
    return out


def gen_unanswerable(llm, papers, target, done_keys, passage_index):
    """Questions that look in-domain but cannot be answered from the corpus.

    Two rounds: round 2 only fills the shortfall after the similarity check.
    """
    titles = "\n".join(f"- {p['paper']}: {p['title']}" for p in papers)
    system = (
        "You create 'unanswerable' QA items for a RAG evaluation dataset. "
        "Given the list of documents in the knowledge base, generate questions that a reader "
        "of these documents might plausibly ask but that CANNOT be answered from them "
        "(topics not covered, papers not in the list, methods only mentioned by name, "
        "facts postdating the documents). "
        "They must look stylistically identical to answerable questions about the corpus. "
        "Do NOT ask about the listed papers or their internal details, and do NOT use terms "
        "from their titles. Prefer clearly out-of-scope fields (e.g., parameter-efficient "
        "fine-tuning, RLHF alignment, multimodal RAG, vector database internals, specific "
        "benchmark leaderboards) and papers that are NOT in the list."
    )
    out, used = [], []
    all_passages = [p for paper in papers for p in paper["passages"]]
    key = ("unanswerable", "batch1")

    for round_no in (1, 2):
        if len(out) >= target:
            break
        exclusion = "\n".join(f"- {q}" for q in used) or "(none)"
        human = (f"KNOWLEDGE BASE DOCUMENTS:\n{titles}\n\n"
                 f"Generate 25 unanswerable questions.\n\n"
                 f"ALREADY GENERATED (do not repeat or paraphrase):\n{exclusion}")
        try:
            r = gen_call(llm, UnanswerableList, system, human)
        except Exception as e:
            print(f"    [skip] generation failed: {e}")
            break
        for q in r.questions:
            if len(out) >= target:
                break
            if any(q.lower()[:40] == u.lower()[:40] for u in used):
                continue
            used.append(q)
            if not collector_check_unanswerable(q, passage_index):
                print(f"    [replace] too similar to corpus: {q[:60]}")
                continue
            out.append({
                "_key": list(key) + [q[:40]],
                "category": "unanswerable",
                "question": q,
                "ground_truth": "知识库中不包含回答该问题所需的内容。正确行为是明确说明未找到相关信息，不得编造。",
                "gold_evidence": [],
                "provenance": "extractive",
                "source_papers": [],
                "source_sections": [],
                "expected_intent": "single_hop",
                "expected_behavior": "refusal",
                "audit": {},
            })

    for it in out:
        done_keys.add(tuple(it["_key"]))
    return out


def collector_check_unanswerable(question, passage_index):
    """In-memory semantic check: top-1 passage must not be strongly related."""
    emb = get_embed()
    qv = emb.embed_query(question)
    best = max((cosine(qv, pv) for pv, _ in passage_index), default=0.0)
    return best < 0.68


# ---------- Phase 4: verification ----------

def verify_items(llm, items, passage_embeddings):
    """LLM judge: does gold_evidence support ground_truth? Flags, never drops."""
    answerable = [it for it in items if it["expected_behavior"] == "answer"]
    print(f"[verify] {len(answerable)} answerable items", flush=True)
    for it in answerable:
        if it.get("verification"):
            continue
        evidence = "\n\n".join(f"- {e}" for e in it["gold_evidence"]) or "(no evidence)"
        system = (
            "You are a QA dataset auditor. Given the evidence excerpts and a claimed "
            "ground truth, decide whether the evidence is sufficient to support the "
            "ground truth. Be strict: any fact in the ground truth that is not in the "
            "evidence makes supported=false."
        )
        human = (f"QUESTION:\n{it['question']}\n\nEVIDENCE:\n{evidence}\n\n"
                 f"CLAIMED GROUND TRUTH:\n{it['ground_truth']}")
        try:
            r = gen_call(llm, VerifyVerdict, system, human)
            it["verification"] = {"supported": r.supported, "reason": r.reason}
        except Exception as e:
            it["verification"] = {"supported": None, "reason": f"judge failed: {e}"}
        status = "✓" if it["verification"]["supported"] else ("✗" if it["verification"]["supported"] is False else "?")
        print(f"    [{status}] {it['question'][:60]}", flush=True)
        time.sleep(0.3)


# ---------- Phase 5: assemble ----------

def assemble(items, run_id):
    by_cat = defaultdict(list)
    for it in items:
        it["query_type"] = it.pop("category")   # 规范字段名（YAML 规格用 query_type）
        by_cat[it["query_type"]].append(it)
    final, overflow = [], []
    for cat, prefix in ID_PREFIX.items():
        pool = by_cat.get(cat, [])
        # verify 支持的优先入选；超产条目进入审核清单备选区
        pool.sort(key=lambda x: 0 if (x.get("verification") or {}).get("supported") else 1)
        chosen = pool[:CATEGORY_TARGETS[cat]]
        overflow += pool[CATEGORY_TARGETS[cat]:]
        for i, it in enumerate(sorted(chosen, key=lambda x: x["question"]), start=1):
            it["id"] = f"{prefix}-{i:03d}"
            it.setdefault("review_status", "pending")
            it.setdefault("notes", "")
            final.append(it)

    data = {
        "version": 1,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "generator": "scripts/generate_golden_dataset.py (draft + LLM verify, 人工审核后冻结)",
        "counts": {cat: min(len(by_cat.get(cat, [])), CATEGORY_TARGETS[cat]) for cat in CATEGORY_TARGETS},
        "items": final,
    }
    OUT_YAML.parent.mkdir(parents=True, exist_ok=True)
    OUT_YAML.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=110),
                        encoding="utf-8")

    review = ["# Golden Dataset 审核清单（草稿）", "",
              f"生成时间: {data['created_at']} | 正式集 {len(final)} 条 | 备选 {len(overflow)} 条",
              "逐条核对: 问题 / 证据 / 答案 三点对读", ""]
    for it in final:
        verdict = it.get("verification", {})
        review.append(f"## {it['id']} [{it['query_type']}] intent={it['expected_intent']} "
                      f"verify={'✓' if verdict.get('supported') else ('✗ ' + verdict.get('reason', '')) if verdict else 'n/a'}")
        review.append(f"- **Q**: {it['question']}")
        for j, e in enumerate(it["gold_evidence"], 1):
            review.append(f"- **证据{j}**: {e[:400]}")
        review.append(f"- **GT**: {it['ground_truth']}")
        review.append(f"- 来源: {', '.join(it['source_papers']) or '(无)'} | 备注: {it.get('notes', '')}")
        review.append("")
    if overflow:
        review.append("---")
        review.append("# 备选（未入选正式集，人工审核后可替换正式集中的 rejected 条目）")
        for it in overflow:
            review.append(f"## 备选 [{it['query_type']}] (verify={bool((it.get('verification') or {}).get('supported'))})")
            review.append(f"- **Q**: {it['question']}")
            review.append(f"- **GT**: {it['ground_truth']}")
            review.append(f"- 来源: {', '.join(it['source_papers']) or '(无)'}")
            review.append("")
    REVIEW_MD.write_text("\n".join(review), encoding="utf-8")
    return OUT_YAML, REVIEW_MD


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="每类目生成上限（调试用）")
    ap.add_argument("--no-verify", action="store_true", help="跳过 LLM 校验 pass")
    ap.add_argument("--fresh", action="store_true", help="忽略 items.jsonl 重头生成")
    args = ap.parse_args()

    GEN_DIR.mkdir(parents=True, exist_ok=True)
    done_keys = set()
    items = []
    if ITEMS_JSONL.exists() and not args.fresh:
        for line in ITEMS_JSONL.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                items.append(rec)
                if rec.get("_key"):
                    done_keys.add(tuple(rec["_key"]))
        print(f"[resume] {len(items)} items already generated", flush=True)

    print("[1/5] inventory...", flush=True)
    papers = load_inventory()
    for p in papers:
        print(f"  {p['paper']}: {p['title'][:60]} ({len(p['passages'])} passages)", flush=True)

    print("[2/5] embeddings...", flush=True)
    # unanswerable 语义检查的嵌入：每篇均匀采样 ≤12 条（与运行中 app 共享 GPU，控制嵌入规模）
    checked = []
    for p in papers:
        ps = p["passages"]
        step = max(1, len(ps) // 12)
        checked += [(p, ps[i]) for i in range(0, len(ps), step)][:12]
    passage_vecs = embed_texts([passage["text"] for _, passage in checked])
    passage_index = list(zip(passage_vecs, checked))
    abstract_vecs = {p["paper"]: embed_texts([" ".join(pp["text"] for pp in p["passages"][:2])[:1200]])[0]
                     for p in papers}

    # 配对选择：锚点优先 + 相似度排序（去掉过高相似的），论文出场次数封顶
    sims = []
    for i in range(len(papers)):
        for j in range(i + 1, len(papers)):
            sims.append((cosine(abstract_vecs[papers[i]["paper"]], abstract_vecs[papers[j]["paper"]]),
                         papers[i]["paper"], papers[j]["paper"]))
    sims.sort(reverse=True)
    anchors = {frozenset(pr) for pr in ANCHOR_PAIRS if all(pid in abstract_vecs for pid in pr)}
    pair_order = [pr for pr in [(b, a) for s, a, b in sims] if frozenset(pr) in anchors]
    pair_order += [pr for s, a, b in sims if 0.35 <= s <= 0.93 and frozenset((a, b)) not in anchors
                   for pr in [(a, b)]]
    degree = Counter()
    selected_pairs = []
    for pa, pb in pair_order:
        if degree[pa] >= 4 or degree[pb] >= 4:
            continue
        selected_pairs.append((pa, pb))
        degree[pa] += 1
        degree[pb] += 1
        if len(selected_pairs) >= 60:
            break
    print(f"[pairs] selected {len(selected_pairs)} (anchors first)", flush=True)

    llm = make_llm()
    limit = args.limit

    print("[3/5] generate...", flush=True)
    t_spf = min(CATEGORY_TARGETS["single_paper_factual"], limit) if limit else CATEGORY_TARGETS["single_paper_factual"]
    n_cmp = min(25, limit) if limit else 25
    n_mh = min(25, limit) if limit else 25
    n_tam = min(10, limit) if limit else 10
    n_una = min(15, limit) if limit else 15

    cmp_pairs = selected_pairs[:n_cmp]
    mh_pairs = selected_pairs[n_cmp:n_cmp + n_mh]

    items += gen_single_paper(llm, papers, t_spf, done_keys)
    items += gen_pair_questions(llm, papers, cmp_pairs, n_cmp, "cross_paper_comparison", done_keys)
    items += gen_pair_questions(llm, papers, mh_pairs, n_mh, "cross_paper_multi_hop", done_keys)
    items += gen_term_ambiguity(llm, papers, None, n_tam, done_keys)
    items += gen_unanswerable(llm, papers, n_una, done_keys, passage_index)

    GEN_DIR.mkdir(parents=True, exist_ok=True)
    with open(ITEMS_JSONL, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    print(f"[gen] {len(items)} items written to {ITEMS_JSONL}", flush=True)

    if not args.no_verify:
        print("[4/5] verify...", flush=True)
        verify_items(llm, items, passage_index)
        with open(ITEMS_JSONL, "w", encoding="utf-8") as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")

    print("[5/5] assemble...", flush=True)
    out_yaml, review = assemble(items, run_id="")
    counts = Counter(it["category"] for it in items)
    print(f"[done] {OUT_YAML}")
    print(f"[done] {review}")
    print(f"[done] counts: {dict(counts)} (targets: {CATEGORY_TARGETS})")
    if any(counts[c] < CATEGORY_TARGETS[c] for c in CATEGORY_TARGETS):
        print("[warn] 部分类目未达标（LLM 生成失败/过滤），重跑脚本可补齐（resume 语义）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
