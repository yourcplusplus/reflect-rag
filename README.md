# ReflectRAG

English | [简体中文](README.zh-CN.md)

An agentic RAG system built on LangGraph, featuring three-stage hybrid retrieval, dual-track self-reflection, and an enforced citation system.

This project is an architectural redesign based on [agentic-rag-for-dummies](https://github.com/GiovanniPasq/agentic-rag-for-dummies).

---

## Key Modifications

| Module | Upstream | ReflectRAG |
|---|---|---|
| Retrieval | BM25 + dense hybrid | + BGE-Reranker refinement (three-stage) |
| Generation-layer reflection | none | Critique node (IsSup + IsUse, bounded retry) |
| Query routing | none | Three-intent router (FAQ / single-hop / multi-hop) |
| Citations | none | Enforced `[chunk_id]` citations + coverage retry |
| Observability | none | Structured trace (8 event types) |
| Ablation | none | V0–V3 switchable configuration |

## Evaluation Results

| Metric | Value | Notes |
|---|---|---|
| MRR | 0.967 | paper-level retrieval |
| Retrieval match rate | 88.2% | gold source found in top-10 |
| RAGAS Faithfulness | 0.86 / 0.95 | classic papers / 2026 papers |
| Citation coverage | 0.89 | share of factual sentences carrying `[chunk_id]`; 0.95 for the FAQ path |
| Multi-hop latency | 33s → 19s | compression-threshold tuning + critique skip, −42% |
| Intent routing accuracy | 77% | three-class classification |

## Architecture

```mermaid
flowchart LR
    Q[User Query] --> IR[Intent Router]
    IR -->|simple_faq| FAQ[Dense Retrieval]
    IR -->|single_hop| SH[Hybrid Retrieval + Rerank]
    IR -->|multi_hop| MH[Agentic Retrieval Loop]
    FAQ --> EG[Evidence Gate]
    SH --> EG
    MH --> EG
    EG --> GEN[Generate]
    GEN --> CR[Critique<br/>IsSup + IsUse]
    CR --> AGG[Aggregate<br/>+ Citation Coverage Check]
```

The intent router classifies each turn before any retrieval work happens. `simple_faq` takes a single dense lookup; `single_hop` runs the full hybrid pipeline with reranking; `multi_hop` enters the agentic loop with budgeted tool calls. Answers from every path converge at an Evidence Gate (hallucination veto), pass through the generation layer and the Critique node, and are finally aggregated with a citation-coverage check.

## Technical Implementation

### Three-stage retrieval

Recall stage fuses BM25 sparse signals with BGE-M3 dense embeddings through Qdrant's RRF hybrid search (2× over-fetch). The refinement stage scores every candidate with a BGE-Reranker-v2-m3 cross-encoder and keeps the top-k. The context stage expands winners through a parent-child index: child chunks drive precise matching, while parent chunks provide full-context evidence to the generator.

### Dual-track self-reflection

The retrieval track is an Evidence Gate: every drafted answer is checked for factual contradictions against the retrieved contexts. The generation track is a Critique node running two checks — IsSup (every factual claim must be supported by the evidence) and IsUse (the answer must actually address the question). Failed checks trigger one bounded retry with structured feedback; a circuit breaker caps the retry budget at 2.

### Enforced citations

The generation layer must attach a `[parent_id]` citation marker to every factual statement; statements without citable evidence must be omitted. The aggregation layer then scans the answer, computes citation coverage over its factual sentences, and — when more than 30% of those sentences lack a `[chunk_id]` marker — triggers one coverage retry before falling back to an explicit "no direct evidence" annotation.

## Ablation Study

| Variant | Configuration | MRR | Latency |
|---|---|---|---|
| V0 | dense only | 0.750 | 8.3s |
| V1 | + BM25 | 0.715 | 7.8s |
| V2 | + Reranker | 0.740 | 8.4s |
| V3 | + Critique + Citations | 0.967 | 11.1s |

**Key finding:** the Critique + citation system raises MRR from 0.74 to 0.967.

### RAGAS Evaluation

| Metric | Group A (Classic Papers) | Group B (2026 Papers) |
|---|---|---|
| RAGAS Faithfulness | 0.86 | 0.95 |
| Context Recall | 0.85 | 0.76 |
| Answer Relevancy | 0.76 | 0.68 |
| Answer Correctness | 0.57 | 0.56 |
| Context Precision | 0.45 | 0.34 |

Group A: 24 classic papers (2022-2024). Group B: 10 papers from 2026. Evaluated with RAGAS framework.

## Quick Start

```bash
git clone https://github.com/yourcplusplus/reflect-rag
cd reflect-rag

uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt
```

Configure `project/.env` (`DEEPSEEK_API_KEY` + `HF_ENDPOINT`), then:

```bash
python project/app.py
```

Run an evaluation pass:

```bash
TRACE_ENABLED=true python evals/run_eval.py --variant V3
```

## REST API

The Gradio app stays as it is; `project/api/` adds a FastAPI service layer on
top of the same `RAGSystem` — same retrieval, same reflection, same citations —
plus conversation persistence (PostgreSQL) and caching (Redis). LangGraph
checkpoints are persisted in the same PostgreSQL via `PostgresSaver`, so agent
memory and pending clarification interrupts survive a restart.

```
project/api/
├── main.py             FastAPI app, lifespan (PostgresSaver), /health, cache stats
├── deps.py             app state + DB session / cache / RAG service dependencies
├── schemas.py          Pydantic request/response + SSE event models
├── cache.py            Redis: answer cache (TTL 1h + jitter) + embedding cache
├── llm_retry.py        tenacity retry/backoff around LLM calls + fallback
├── rate_limit.py       per-IP Redis INCR/EXPIRE limiter for POST /api/v1/chat
├── patches.py          runtime shims (embedding cache, Qdrant server mode)
├── db/                 SQLAlchemy models (conversations, messages, documents)
├── migrations/         Alembic revisions
├── services/           RAG lifecycle + LangGraph stream → API events
└── routers/            chat, documents, conversations
```

### Run it locally

```bash
pip install -r requirements-api.txt          # on top of requirements.txt

# once: create the schema (needs PostgreSQL; DATABASE_URL, default localhost:5432)
alembic upgrade head

# start the API (from project/, or with --app-dir project from the root)
cd project && uvicorn api.main:app --port 8000
```

Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs).

| Endpoint | Notes |
|---|---|
| `POST /api/v1/chat` | SSE stream: `conversation`, `cache`, `status`, `node`, `tool_call`, `tool_result`, `tool_skipped`, `token`, `done` |
| `POST /api/v1/documents` | Multipart upload (`.pdf`, `.md`) → 202 + Redis List queue entry (a worker indexes it) |
| `GET /api/v1/documents/{id}` | Task state: `pending` → `indexing` → `indexed` / `failed` (+ `attempts`, `error`) |
| `GET /api/v1/documents` | Registered documents + `indexed_sources` (what is in the knowledge base) |
| `GET /api/v1/queues/stats` | Queue depth (`doc:ingest:queue` / `processing`) + per-status counts |
| `GET /api/v1/conversations` | Conversations with message counts and last-message previews |
| `GET /api/v1/conversations/{id}/messages` | Full transcript of one conversation |
| `GET /health` | Per-component readiness (RAG / PostgreSQL / Redis / Qdrant); 503 until the models are loaded |
| `GET /api/v1/cache/stats` | Cache hit/miss counters and key counts |

```bash
curl -N -X POST http://localhost:8000/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "What problem does DPR solve?"}'
```

### Async document ingestion (Redis List queue)

`POST /api/v1/documents` only enqueues; a separate worker does the heavy lifting.

**Producer.** For each upload the API stores the file under `uploads/`, computes
its SHA-256 (`content_hash`), inserts a `documents` row with `status=pending`
(a unique index on `content_hash` enforces one row per content), and `LPUSH`es
the document id onto `doc:ingest:queue`. The response is **202** with the
per-file outcome (`queued` / `deduplicated`); no parsing, chunking or embedding
happens inside the request. If `LPUSH` still fails after its retries, the row is
marked `failed` with error `投递队列失败` and the endpoint returns 503 — the API
never reports a document as queued when it is not.

**Consumer.** `worker.py` runs one loop:

1. `BRPOPLPUSH doc:ingest:queue doc:ingest:processing` — atomically reserve one
   id. This is the first half of a manual ACK: the task stays visible in
   `processing` while it runs.
2. Commit `status=indexing`, then convert (PDF→Markdown), chunk, embed with
   BGE-M3 and write to Qdrant. Re-indexing deletes the document's old chunks
   before writing the new ones.
3. Commit `status=indexed` and `LREM` the id from `processing` — the second half
   of the ACK.

One consumer is deliberate: the embedding model is the bottleneck, and
re-indexing a single document must be serial.

**Reliability.** Redis is a transport; the state machine lives in PostgreSQL:
`pending → indexing → indexed`, with `failed` as the dead-letter state.

- **Worker crash**: the id is still in `processing`. On startup `recover()`
  requeues `pending` ids and `indexing` ids whose `updated_at` is older than
  `INGEST_STALE_SECONDS` (default 600s); it acks ids that are already terminal.
  A *fresh* `indexing` row is left alone because it may belong to another live
  worker.
- **Retries**: a failure increments `attempts`, resets the row to `pending` and
  requeues with exponential backoff (`INGEST_BACKOFF_SECONDS * 2^(n-1)`, base 1s
  by default). At `INGEST_MAX_ATTEMPTS` (default 3) the row becomes `failed`;
  re-uploading the same bytes resets it and enqueues again.
- **Idempotency**: `content_hash` is unique, so uploading identical bytes
  returns the existing `document_id` (`deduplicated: true`) and deletes the
  duplicate file; concurrent uploads race safely — the losing INSERT hits the
  unique index and returns the winner's row. The worker also acks ids that are
  already `indexed`/`skipped` and ignores `failed` rows that exhausted attempts.

> Queue durability follows Redis persistence: with `--appendonly no` a Redis
> restart drops queued ids and leaves rows in `pending`. `docker-compose.yml`
> therefore runs Redis with AOF enabled; do the same if you self-host it.

**Why a Redis List, not Celery/RabbitMQ.** Redis is already in the stack
(answer cache, embedding cache, rate limiting), so the queue adds no broker
process to run or monitor. Task state stays in PostgreSQL where it is queryable
(`GET /documents/{id}`, `GET /queues/stats`), and `BRPOPLPUSH` + explicit `LREM`
give manual acknowledgement without a framework — we control exactly when a
task counts as done, and stale detection is one timestamp comparison. The cost
is no priorities, scheduling, routing or built-in retries; for one queue and one
worker that is a small amount of explicit code instead of more infrastructure.

**Switching to Celery later.** `IngestQueue.enqueue()` is the only producer
surface, and PostgreSQL already owns the state machine, so the migration is
contained: publish a Celery task from that method, let the task call
`DocumentIndexer.index` (unchanged), and let `acks_late` + `visibility_timeout`
replace the `processing` list and stale scan. Keep `content_hash` and the status
transitions as the idempotency guard, and duplicate deliveries stay harmless.

**Running the worker.** Qdrant must run as a server (`QDRANT_URL`): the embedded
local database takes an exclusive file lock, so a second process cannot share
it. Without `QDRANT_URL` the API returns 503 on upload and the worker exits with
a clear error.

```bash
# dependencies: Qdrant server + PostgreSQL + Redis
docker compose up -d qdrant postgres redis
cd project && alembic upgrade head && cd ..     # schema (once)

export DATABASE_URL=postgresql+psycopg://reflect:reflect@localhost:5432/reflect_rag
export REDIS_URL=redis://localhost:6379/0
export QDRANT_URL=http://localhost:6333
python worker.py                                # from the repository root

# or containerised:
docker compose up -d worker
```

Tunables: `INGEST_MAX_ATTEMPTS` (3), `INGEST_BACKOFF_SECONDS` (1),
`INGEST_STALE_SECONDS` (600), `INGEST_POLL_TIMEOUT` (5),
`INGEST_ENQUEUE_RETRIES` (3).

```bash
curl -s -X POST http://localhost:8000/api/v1/documents -F 'files=@paper.pdf'   # 202, status=pending
curl -s http://localhost:8000/api/v1/documents/<document_id>                   # poll
curl -s http://localhost:8000/api/v1/queues/stats
```

The first turn runs the graph and is written to `messages`; repeating the same
question with the same conversation history is served from Redis (TTL 1h).
Concurrent duplicates are coalesced by a process-local singleflight: one leader
generates, the rest wait and re-read the cached answer. Each conversation maps
to its own LangGraph checkpoint thread, so `conversation_id` carries agent
memory across turns (with `CHECKPOINT_BACKEND=postgres` the checkpoint lives in
PostgreSQL and survives a restart; otherwise it is in-memory for the process
lifetime); send `"use_cache": false` to force a fresh run.

### Docker Compose (API + PostgreSQL + Redis + Qdrant)

```bash
docker compose up --build      # first boot downloads BGE-M3 + the reranker (~4.5 GB)
curl http://localhost:8000/health
```

Compose starts the Qdrant **server** and sets `QDRANT_URL` for the API; the API
redirects the core's `QdrantClient(path=...)` to it (see `project/api/patches.py`),
which is what lets the API and the Gradio UI share one index. Without
`QDRANT_URL` the core keeps using embedded local-mode Qdrant — that mode takes an
exclusive file lock, so run only one process at a time against `qdrant_db/`.

Redis is optional everywhere: if it is unreachable the API logs a warning and
answers without caching (`/health` reports `degraded`). No RAG core file
(`core/`, `rag_agent/`, `db/`) was modified for any of this.

## Tech Stack

LangGraph · LangChain · Qdrant · BGE-M3 · BGE-Reranker-v2-m3 · DeepSeek API · Gradio · RAGAS · FastAPI · PostgreSQL · Redis · Docker

## Known Limitations

- On WSL2, GPU passthrough can intermittently segfault; development in CPU mode is recommended.
- Evaluation figures come from single runs, not repeated sampling.

## Acknowledgements

Based on [agentic-rag-for-dummies](https://github.com/GiovanniPasq/agentic-rag-for-dummies) (MIT License).

## License

MIT License — see [LICENSE](LICENSE).
