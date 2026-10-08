# ReflectRAG

An agentic RAG system built on LangGraph, featuring three-stage hybrid retrieval, dual-track self-reflection, and an enforced citation system.

This is the Python application package. See the [root README](../README.md) for the architecture overview, evaluation results, and the ablation study.

## Project Structure

```
project/
├── app.py                  # Entry point (Gradio UI)
├── config.py               # Central configuration (models, retrieval, agent, tracing)
├── core/                   # RAGSystem, ChatInterface, DocumentManager, Tracing, Logging
├── db/                     # Qdrant vector store + parent-store managers
├── rag_agent/              # LangGraph nodes, edges, prompts, tools, state schemas
├── ui/                     # Gradio app + CSS
├── document_chunker.py     # Parent-child hierarchical chunking
└── utils.py                # PDF→Markdown conversion and token helpers
```

## Installation

```bash
cd reflect-rag

uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt
```

For GPU machines whose driver supports CUDA 12.4 only, install the cu124 torch
build first, then the rest (see `requirements-cuda.txt`):

```bash
pip install -r requirements-cuda.txt --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
```

## Configuration

Create `project/.env`:

```bash
DEEPSEEK_API_KEY=sk-xxxxxxxx
HF_ENDPOINT=https://hf-mirror.com   # optional mirror for model downloads
```

Key settings in `config.py`:

| Setting | Default | Purpose |
|---|---|---|
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | LLM endpoint |
| `LLM_MODEL` | `deepseek-chat` | Generation model |
| `DENSE_MODEL` | `BAAI/bge-m3` | Dense embeddings |
| `RERANKER_MODEL` | `BAAI/bge-reranker-v2-m3` | Cross-encoder refinement |
| `DEFAULT_RETRIEVAL_K` | `7` | Final chunks per search |
| `RERANKER_TOP_K_MULTIPLIER` | `2` | Recall over-fetch factor |
| `RETRIEVAL_SCORE_THRESHOLD` | `0.4` | Minimum fused score |

## Running

```bash
python project/app.py
```

The Gradio interface opens at `http://127.0.0.1:7860`. Upload PDF or Markdown
documents in the **Documents** tab, then chat in the **Chat** tab.

## Environment Switches (Ablation)

| Variable | Default | Effect |
|---|---|---|
| `DEFAULT_RETRIEVAL_MODE` | `hybrid` | `hybrid` / `sparse` / `dense` |
| `ENABLE_RERANKER` | `true` | Toggle the BGE-Reranker stage |
| `ENABLE_CRITIQUE` | `true` | Toggle the generation-layer Critique node |
| `TRACE_ENABLED` | `false` | Write per-request traces to `evals/results/traces/` |

Example — full ablation variant V0 (pure dense, no reranker, no critique):

```bash
DEFAULT_RETRIEVAL_MODE=dense ENABLE_RERANKER=false ENABLE_CRITIQUE=false \
  python project/app.py
```

## Evaluation

```bash
TRACE_ENABLED=true python evals/run_eval.py --variant V3 --limit 30
python evals/ragas_backfill.py --results evals/results/runs/V3/<stamp>/results.json
python evals/compare.py
```

See `evals/` for the golden dataset, RAGAS backfill, and variant comparison tools.
