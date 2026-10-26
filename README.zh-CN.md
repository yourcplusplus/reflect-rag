# ReflectRAG

[English](README.md) | 简体中文

基于 LangGraph 的 Agentic RAG 系统，具备三阶段混合检索、双轨自反思与强制引用机制。

本项目在 [agentic-rag-for-dummies](https://github.com/GiovanniPasq/agentic-rag-for-dummies) 的基础上做了架构级重构。

---

## 主要改动

| 模块 | 上游实现 | ReflectRAG |
|---|---|---|
| 检索 | BM25 + 稠密向量混合检索 | 增加 BGE-Reranker 精排（三阶段） |
| 生成层反思 | 无 | Critique 节点（IsSup + IsUse，有界重试） |
| 查询路由 | 无 | 三分类意图路由（FAQ / 单跳 / 多跳） |
| 引用 | 无 | 强制 `[chunk_id]` 引用 + 覆盖率重试 |
| 可观测性 | 无 | 结构化 Trace（8 类事件） |
| 消融实验 | 无 | V0–V3 可切换配置 |

## 评测结果

| 指标 | 数值 | 说明 |
|---|---|---|
| MRR | 0.967 | 论文级检索 |
| 检索匹配率 | 88.2% | gold source 命中 top-10 |
| RAGAS Faithfulness | 0.86 / 0.95 | 经典论文集 / 2026 年论文集 |
| 引用覆盖率 | 0.89 | 携带 `[chunk_id]` 的事实句占比；FAQ 路径为 0.95 |
| 多跳延迟 | 33s → 19s | 压缩阈值调优 + Critique 跳过，−42% |
| 意图路由准确率 | 77% | 三分类 |

## 架构

```mermaid
flowchart LR
    Q[用户问题] --> IR[意图路由]
    IR -->|simple_faq| FAQ[稠密检索]
    IR -->|single_hop| SH[混合检索 + 精排]
    IR -->|multi_hop| MH[Agentic 检索循环]
    FAQ --> EG[证据门禁]
    SH --> EG
    MH --> EG
    EG --> GEN[生成]
    GEN --> CR[Critique<br/>IsSup + IsUse]
    CR --> AGG[聚合<br/>+ 引用覆盖率检查]
```

意图路由会在任何检索动作发生之前先对每一轮提问分类。`simple_faq` 只做一次稠密检索；`single_hop` 走完整的混合检索 + 精排流水线；`multi_hop` 进入带预算限制的工具调用循环。所有路径生成的答案都汇入证据门禁（幻觉否决），再经过生成层与 Critique 节点，最后在聚合层做引用覆盖率检查。

## 技术实现

### 三阶段检索

召回阶段通过 Qdrant 的 RRF 混合检索（2× 过采样）融合 BM25 稀疏信号与 BGE-M3 稠密向量。精排阶段用 BGE-Reranker-v2-m3 跨编码器对每个候选打分并保留 top-k。上下文阶段通过父子索引展开：child chunk 负责精确匹配，parent chunk 为生成器提供完整上下文证据。

### 双轨自反思

检索轨是证据门禁：每份草稿答案都会对照检索到的上下文做事实矛盾检查。生成轨是 Critique 节点，执行两项检查——IsSup（每一条事实性声明都必须有证据支撑）与 IsUse（答案必须真正回应问题）。检查失败会带着结构化反馈触发一次有界重试；熔断器把重试预算限制在 2 次。

### 强制引用

生成层必须为每条事实性声明附加 `[parent_id]` 引用标记；无法归因到证据的声明必须删除。聚合层随后扫描答案，统计其事实句的引用覆盖率——当超过 30% 的事实句缺少 `[chunk_id]` 标记时，触发一次覆盖率重试；若仍不达标，则显式标注"未找到直接证据"。

## 消融实验

| 变体 | 配置 | MRR | 延迟 |
|---|---|---|---|
| V0 | 仅稠密检索 | 0.750 | 8.3s |
| V1 | + BM25 | 0.715 | 7.8s |
| V2 | + Reranker | 0.740 | 8.4s |
| V3 | + Critique + 强制引用 | 0.967 | 11.1s |

**关键结论：** Critique + 强制引用机制将 MRR 从 0.74 提升至 0.967。

### RAGAS 评测

| 指标 | Group A（经典论文） | Group B（2026 论文） |
|---|---|---|
| RAGAS Faithfulness | 0.86 | 0.95 |
| Context Recall | 0.85 | 0.76 |
| Answer Relevancy | 0.76 | 0.68 |
| Answer Correctness | 0.57 | 0.56 |
| Context Precision | 0.45 | 0.34 |

Group A：24 篇经典论文（2022–2024）。Group B：10 篇 2026 年论文。均使用 RAGAS 框架评测。

## 快速开始

```bash
git clone https://github.com/yourcplusplus/reflect-rag
cd reflect-rag

uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt
```

配置 `project/.env`（`DEEPSEEK_API_KEY` + `HF_ENDPOINT`），然后运行：

```bash
python project/app.py
```

跑一轮评测：

```bash
TRACE_ENABLED=true python evals/run_eval.py --variant V3
```

## REST API

Gradio 应用保持不变；`project/api/` 在同一套 `RAGSystem` 之上增加了 FastAPI 服务层——相同的检索、相同的反思、相同的引用机制——另外加上会话持久化（PostgreSQL）与缓存（Redis）。LangGraph 的 checkpoint 通过 `PostgresSaver` 持久化到同一个 PostgreSQL，因此 Agent 记忆与待处理的澄清中断在重启后仍然保留。

```
project/api/
├── main.py              FastAPI 应用、lifespan（PostgresSaver）、/health、缓存统计
├── deps.py              应用状态 + 数据库会话 / 缓存 / RAG 服务依赖
├── schemas.py           Pydantic 请求/响应 + SSE 事件模型
├── cache.py             Redis：答案缓存（TTL 1h + 抖动）+ 向量缓存
├── llm_retry.py         基于 tenacity 的 LLM 重试/退避 + 降级
├── rate_limit.py        按 IP 的 Redis INCR/EXPIRE 限流（POST /api/v1/chat）
├── patches.py           运行时 shim（向量缓存、Qdrant 服务端模式）
├── db/                  SQLAlchemy 模型（conversations、messages、documents）
├── migrations/          Alembic 迁移
├── services/            RAG 生命周期 + LangGraph 流 → API 事件
└── routers/             chat、documents、conversations
```

### 本地运行

```bash
pip install -r requirements-api.txt          # 在 requirements.txt 之上
# 首次：创建表结构（需要 PostgreSQL；DATABASE_URL，默认 localhost:5432）
alembic upgrade head

# 启动 API（在 project/ 下执行，或在根目录加 --app-dir project）
cd project && uvicorn api.main:app --port 8000
```

交互式文档：[http://localhost:8000/docs](http://localhost:8000/docs)。

| 端点 | 说明 |
|---|---|
| `POST /api/v1/chat` | SSE 流：`conversation`、`cache`、`status`、`node`、`tool_call`、`tool_result`、`tool_skipped`、`token`、`done` |
| `POST /api/v1/documents` | 多文件上传（`.pdf`、`.md`）→ 202 + 投递 Redis List 队列（由 worker 索引） |
| `GET /api/v1/documents/{id}` | 任务状态：`pending` → `indexing` → `indexed` / `failed`（含 `attempts`、`error`） |
| `GET /api/v1/documents` | 已登记文档 + `indexed_sources`（当前知识库内容） |
| `GET /api/v1/queues/stats` | 队列深度（`doc:ingest:queue` / `processing`）+ 各状态计数 |
| `GET /api/v1/conversations` | 会话列表，含消息数与最后一条消息预览 |
| `GET /api/v1/conversations/{id}/messages` | 某个会话的完整记录 |
| `GET /health` | 各组件就绪状态（RAG / PostgreSQL / Redis / Qdrant）；模型加载完成前返回 503 |
| `GET /api/v1/cache/stats` | 缓存命中/未命中计数与 key 数量 |

```bash
curl -N -X POST http://localhost:8000/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "What problem does DPR solve?"}'
```

### 异步文档入库（Redis List 队列）

`POST /api/v1/documents` 只负责入队，真正的重活由独立的 worker 完成。

**生产端。** 每次上传时，API 把文件存到 `uploads/`，计算其 SHA-256（`content_hash`），插入一条 `status=pending` 的 `documents` 记录（`content_hash` 上的唯一索引保证一份内容只有一行），并把 document id `LPUSH` 到 `doc:ingest:queue`。响应为 **202**，附带每个文件的处理结果（`queued` / `deduplicated`）；请求内不做任何解析、分块或向量化。如果 `LPUSH` 重试后仍失败，该行会被标记为 `failed`（错误信息 `投递队列失败`），接口返回 503——API 绝不会把没入队的文档报告成已入队。

**消费端。** `worker.py` 运行单循环：

1. `BRPOPLPUSH doc:ingest:queue doc:ingest:processing`——原子地预留一个 id。这是手动 ACK 的第一步：任务执行期间会一直留在 `processing` 中可见。
2. 提交 `status=indexing`，然后做格式转换（PDF→Markdown）、分块、BGE-M3 向量化并写入 Qdrant。重建索引时会先删除该文档的旧 chunk 再写新的。
3. 提交 `status=indexed` 并从 `processing` 中 `LREM`——ACK 的第二步。

刻意只用单个消费者：向量化模型是吞吐瓶颈，而且同一文档的重建必须串行。

**可靠性。** Redis 只是传输层，状态机住在 PostgreSQL：`pending → indexing → indexed`，`failed` 作为死信状态。

- **Worker 崩溃**：id 仍留在 `processing` 中。启动时 `recover()` 会把 `pending` 的 id，以及 `updated_at` 超过 `INGEST_STALE_SECONDS`（默认 600s）的 `indexing` id 重新入队；已经处于终态的 id 直接 ACK。*新鲜*的 `indexing` 记录会被保留，因为它可能属于另一个仍在运行的 worker。
- **重试**：失败时 `attempts` 加一，状态改回 `pending`，并按指数退避重新入队（`INGEST_BACKOFF_SECONDS * 2^(n-1)`，默认基数 1s）。达到 `INGEST_MAX_ATTEMPTS`（默认 3）后转为 `failed`；重新上传相同字节会重置状态并再次入队。
- **幂等**：`content_hash` 唯一，因此上传相同字节会返回已有的 `document_id`（`deduplicated: true`）并删除重复文件；并发上传也能安全竞争——竞争的 INSERT 会撞上唯一索引并返回胜者的记录。worker 也会直接 ACK 已是 `indexed`/`skipped` 的 id，并忽略已达重试上限的 `failed` 记录。

> 队列的持久性取决于 Redis 持久化：使用 `--appendonly no` 时，Redis 重启会丢掉排队中的 id，让记录永远停在 `pending`。因此 `docker-compose.yml` 已为 Redis 启用 AOF；自托管时请做同样配置。

**为什么用 Redis List 而不是 Celery/RabbitMQ。** Redis 本来就在技术栈里（答案缓存、向量缓存、限流），所以队列不需要额外引入一个要运行、要监控的 broker。任务状态保留在 PostgreSQL 中，可直接查询（`GET /documents/{id}`、`GET /queues/stats`）；`BRPOPLPUSH` + 显式 `LREM` 提供了不依赖框架的手动 ACK——任务何时算完成完全由我们控制，僵死检测也只是一次时间戳比较。代价是没有优先级、定时调度、路由和内置重试；对单队列 + 单 worker 的场景，这只是一小段显式代码，而不是更多基础设施。

**以后切换到 Celery。** `IngestQueue.enqueue()` 是唯一的生产端接口，且状态机已在 PostgreSQL 中，所以迁移范围是可控的：在该方法里发布 Celery 任务，任务直接调用 `DocumentIndexer.index`（不改动），并用 `acks_late` + `visibility_timeout` 替代 `processing` 列表与僵死扫描。保留 `content_hash` 与状态流转作为幂等保护，重复投递依然无害。

**运行 worker。** Qdrant 必须以服务端模式运行（`QDRANT_URL`）：嵌入式本地数据库会持有排他文件锁，第二个进程无法共享。没有配置 `QDRANT_URL` 时，API 上传接口返回 503，worker 启动时也会给出明确错误。

```bash
# 依赖：Qdrant 服务端 + PostgreSQL + Redis
docker compose up -d qdrant postgres redis
cd project && alembic upgrade head && cd ..     # 首次创建表结构

export DATABASE_URL=postgresql+psycopg://reflect:reflect@localhost:5432/reflect_rag
export REDIS_URL=redis://localhost:6379/0
export QDRANT_URL=http://localhost:6333
python worker.py                                # 在仓库根目录执行

# 或用容器：
docker compose up -d worker
```

可调参数：`INGEST_MAX_ATTEMPTS`（3）、`INGEST_BACKOFF_SECONDS`（1）、`INGEST_STALE_SECONDS`（600）、`INGEST_POLL_TIMEOUT`（5）、`INGEST_ENQUEUE_RETRIES`（3）。

```bash
curl -s -X POST http://localhost:8000/api/v1/documents -F 'files=@paper.pdf'   # 202, status=pending
curl -s http://localhost:8000/api/v1/documents/<document_id>                   # 轮询
curl -s http://localhost:8000/api/v1/queues/stats
```

第一轮对话会真正执行图并写入 `messages`；在相同会话历史下重复同一个问题会直接由 Redis 返回（TTL 1h）。每个会话对应独立的 LangGraph checkpoint 线程，因此 `conversation_id` 让 Agent 记忆跨轮次延续（`CHECKPOINT_BACKEND=postgres` 时 checkpoint 持久化在 PostgreSQL，否则仅在进程内存中存活）；发送 `"use_cache": false` 可强制重新执行。

### Docker Compose（API + PostgreSQL + Redis + Qdrant）

```bash
docker compose up --build      # 首次启动会下载 BGE-M3 + Reranker（约 4.5 GB）
curl http://localhost:8000/health
```

Compose 会启动 Qdrant **服务端**并为 API 设置 `QDRANT_URL`；API 会把核心里的 `QdrantClient(path=...)` 重定向到该地址（见 `project/api/patches.py`），这也是 API 与 Gradio UI 能共享同一索引的原因。未设置 `QDRANT_URL` 时，核心继续使用嵌入式本地模式——该模式持有排他文件锁，因此同一时间只能有一个进程访问 `qdrant_db/`。

Redis 在所有场景下都是可选的：不可达时 API 记录一条警告并在无缓存的情况下作答（`/health` 报告 `degraded`）。以上改动没有修改任何 RAG 核心文件（`core/`、`rag_agent/`、`db/`）。

## 技术栈

LangGraph · LangChain · Qdrant · BGE-M3 · BGE-Reranker-v2-m3 · DeepSeek API · Gradio · RAGAS · FastAPI · PostgreSQL · Redis · Docker

## 已知限制

- 在 WSL2 下 GPU 直通可能间歇性 segfault；建议用 CPU 模式开发。
- 评测数据来自单次运行，未做重复采样。

## 致谢

基于 [agentic-rag-for-dummies](https://github.com/GiovanniPasq/agentic-rag-for-dummies)（MIT License）。

## 许可证

MIT License — 见 [LICENSE](LICENSE)。
