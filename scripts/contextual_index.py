#!/usr/bin/env python3
"""Contextual Retrieval indexing: generate a short context summary per child
chunk (50-100 tokens, DeepSeek-chat), prepend it, and index into the
dedicated collection config.CONTEXTUAL_COLLECTION.

Two phases (both resumable / idempotent):
  Phase 1  generate summaries -> evals/results/contextual/chunk_contexts.jsonl
  Phase 2  embed enhanced chunks -> Qdrant collection (skipped when complete)

Usage:
  python scripts/contextual_index.py [--limit N] [--workers 8]
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "project"))

from dotenv import load_dotenv
load_dotenv(ROOT / "project" / ".env")

import config
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_deepseek import ChatDeepSeek
from core.rag_system import RAGSystem

OUT_DIR = ROOT / "evals" / "results" / "contextual"
CTX_JSONL = OUT_DIR / "chunk_contexts.jsonl"

def chunk_key(parent_id: str, content: str) -> str:
    return hashlib.md5(f"{parent_id}::{content}".encode("utf-8")).hexdigest()


def build_prompt(source: str, parent_content: str, chunk_content: str) -> list:
    system = (
        "You prepare a retrieval index. Given a document excerpt and one of its chunks, "
        "write a 50-100 token context summary (in the chunk's language) stating where the "
        "chunk sits in the document and what topic it covers, so the chunk can be matched "
        "by topic queries. Output ONLY the summary, no prefixes, no quotes."
    )
    human = (f"Document: {source}\n\nParent context:\n{parent_content[:2000]}\n\n"
             f"Chunk:\n{chunk_content[:1200]}")
    return [SystemMessage(content=system), HumanMessage(content=human)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="只处理前 N 个 chunk（验证用）")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("[1/3] 构建 chunk 清单...", flush=True)
    rs = RAGSystem()
    parent_pairs, child_chunks = rs.chunker.create_chunks()
    parent_content = {pid: doc.page_content for pid, doc in parent_pairs}
    if args.limit:
        child_chunks = child_chunks[: args.limit]
    print(f"  child chunks: {len(child_chunks)} | parents: {len(parent_pairs)}", flush=True)

    # ---- Phase 1: 摘要生成（resume）----
    done = {}
    if CTX_JSONL.exists():
        for line in CTX_JSONL.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                done[rec["key"]] = rec["context"]
        print(f"[resume] 已生成摘要 {len(done)} 条", flush=True)

    todo = []
    for c in child_chunks:
        pid = c.metadata.get("parent_id", "")
        key = chunk_key(pid, c.page_content)
        if key not in done:
            todo.append((key, c))
    print(f"[2/3] 待生成摘要 {len(todo)}/{len(child_chunks)}", flush=True)

    if todo:
        llm = ChatDeepSeek(model=config.LLM_MODEL, api_key=config.DEEPSEEK_API_KEY,
                           api_base=config.DEEPSEEK_BASE_URL, temperature=0, request_timeout=90)
        write_lock = threading.Lock()
        f_out = open(CTX_JSONL, "a", encoding="utf-8")
        counter = {"ok": 0, "fail": 0, "hit": 0, "miss": 0}
        t0 = time.time()

        def work(item):
            key, c = item
            pid = c.metadata.get("parent_id", "")
            try:
                resp = llm.invoke(build_prompt(c.metadata.get("source", ""),
                                               parent_content.get(pid, ""), c.page_content))
                ctx = str(resp.content).strip()
                usage = getattr(resp, "usage_metadata", None) or {}
                return key, ctx, usage, None
            except Exception as e:
                return key, None, {}, str(e)[:200]

        with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
            futures = [ex.submit(work, it) for it in todo]
            for i, fut in enumerate(cf.as_completed(futures), 1):
                key, ctx, usage, err = fut.result()
                if ctx:
                    with write_lock:
                        f_out.write(json.dumps({"key": key, "context": ctx}, ensure_ascii=False) + "\n")
                        f_out.flush()
                    done[key] = ctx
                    counter["ok"] += 1
                    counter["hit"] += usage.get("input_token_details", {}).get("cache_read", 0) or 0
                    counter["miss"] += usage.get("input_tokens", 0) or 0
                else:
                    counter["fail"] += 1
                if i % 50 == 0 or i == len(futures):
                    el = time.time() - t0
                    print(f"  [{i}/{len(futures)}] ok={counter['ok']} fail={counter['fail']} "
                          f"| {el:.0f}s | cache_hit_tokens={counter['hit']} miss={counter['miss']}", flush=True)
        f_out.close()
        print(f"  摘要生成完成: ok={counter['ok']} fail={counter['fail']}", flush=True)

    # ---- Phase 2: 拼接 + 索引到 _ctx collection（幂等重建）----
    print("[3/3] 构建增强 chunk 并写入 collection...", flush=True)
    enhanced = []
    for c in child_chunks:
        pid = c.metadata.get("parent_id", "")
        key = chunk_key(pid, c.page_content)
        ctx = done.get(key)
        if not ctx:
            continue
        enhanced.append(Document(page_content=f"{ctx}\n\n{c.page_content}",
                                 metadata=dict(c.metadata)))
    print(f"  增强 chunk: {len(enhanced)}", flush=True)

    ctx_name = config.CONTEXTUAL_COLLECTION
    existing = rs.vector_db.point_count(ctx_name) if rs.vector_db.collection_exists(ctx_name) else 0
    if existing >= len(enhanced) and existing > 0:
        print(f"  collection '{ctx_name}' 已完整（{existing} 点）——跳过写入", flush=True)
    else:
        if existing > 0:
            print(f"  collection '{ctx_name}' 不完整（{existing} < {len(enhanced)}）——重建", flush=True)
            rs.vector_db.delete_collection(ctx_name)
        rs.vector_db.create_collection(ctx_name)
        collection = rs.vector_db.get_collection(ctx_name)
        batch = 256
        for i in range(0, len(enhanced), batch):
            collection.add_documents(enhanced[i:i + batch])
            print(f"  indexed {min(i + batch, len(enhanced))}/{len(enhanced)}", flush=True)

    final = rs.vector_db.point_count(ctx_name)
    print(f"\nRESULT: collection={ctx_name} points={final} | 摘要缓存={len(done)}", flush=True)


if __name__ == "__main__":
    main()
