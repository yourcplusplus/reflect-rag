import os

# --- Directory Configuration ---
_BASE_DIR = os.path.dirname(os.path.dirname(__file__))

MARKDOWN_DIR = os.path.join(_BASE_DIR, "markdown_docs")
PARENT_STORE_PATH = os.path.join(_BASE_DIR, "parent_store")
QDRANT_DB_PATH = os.path.join(_BASE_DIR, "qdrant_db")

# --- Qdrant Configuration ---
CHILD_COLLECTION = "document_child_chunks"
SPARSE_VECTOR_NAME = "sparse"

# --- Model Configuration ---
DENSE_MODEL = "BAAI/bge-m3"
SPARSE_MODEL = "Qdrant/bm25"
LLM_MODEL = "deepseek-chat"
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
JUDGE_MODEL = "ministral-3:3b-instruct-2512-q8_0"
LLM_TEMPERATURE = 0
LLM_SEED = 42

# --- Retrieval Configuration ---
RETRIEVAL_SCORE_THRESHOLD = 0.4
DEFAULT_RETRIEVAL_K = 7
DEFAULT_RETRIEVAL_MODE = os.environ.get("DEFAULT_RETRIEVAL_MODE", "hybrid")  # hybrid | sparse | dense (dense = V0 pure-vector ablation)
RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
RERANKER_TOP_K_MULTIPLIER = 2
ENABLE_RERANKER = os.environ.get("ENABLE_RERANKER", "true").lower() == "true"
CHILD_CHUNK_SEPARATOR = "\n\n<CHILD_CHUNK_BOUNDARY>\n\n"

# --- Contextual Retrieval & Source Filtering ---
CONTEXTUAL_RETRIEVAL_ENABLED = os.environ.get("CONTEXTUAL_RETRIEVAL_ENABLED", "false").lower() == "true"
CONTEXTUAL_COLLECTION = "document_child_chunks_ctx"
SOURCE_FILTER_ENABLED = os.environ.get("SOURCE_FILTER_ENABLED", "false").lower() == "true"
SOURCE_FILTER_MIN_SCORE = float(os.environ.get("SOURCE_FILTER_MIN_SCORE", "0.0"))
SOURCE_FILTER_MAX_PER_PARENT = int(os.environ.get("SOURCE_FILTER_MAX_PER_PARENT", "2"))

# --- Context Pool Convergence (second-stage rerank over accumulated contexts) ---
CONTEXT_POOL_CONVERGENCE_ENABLED = os.environ.get("CONTEXT_POOL_CONVERGENCE_ENABLED", "true").lower() == "true"
CONTEXT_POOL_TOP_K = int(os.environ.get("CONTEXT_POOL_TOP_K", "7"))

# --- Latency Optimizations (flag-gated) ---
# 默认全关：10 月的基线 run（V0-V3 / conv / ctx 系列）都不含这两个优化，
# 消融配对必须在同样关闭的状态下跑。做"优化后"对照 run 时再显式打开。
# SKIP_SINGLE_ANSWER_SYNTHESIS: 单个 rewritten question 时跳过 aggregate_answers
#   的合成 LLM 调用（纯转写，省 2-4s）；引用覆盖率检查与重试不受影响。
SKIP_SINGLE_ANSWER_SYNTHESIS = os.environ.get("SKIP_SINGLE_ANSWER_SYNTHESIS", "false").lower() == "true"
# MERGED_QUERY_UNDERSTANDING: intent 分类 + query 改写合并为一次结构化调用，
#   入口由两次串行 LLM（~1.5s + ~0.9s）减为一次。澄清轮保持旧行为（只改写）。
MERGED_QUERY_UNDERSTANDING = os.environ.get("MERGED_QUERY_UNDERSTANDING", "false").lower() == "true"

# --- Agent Configuration ---
MAX_TOOL_CALLS = 8
MAX_ITERATIONS = 10
GRAPH_RECURSION_LIMIT = 50
MAIN_HISTORY_MESSAGES_TO_KEEP = 4
ENABLE_CRITIQUE = os.environ.get("ENABLE_CRITIQUE", "true").lower() == "true"
BASE_TOKEN_THRESHOLD = 8000
TOKEN_GROWTH_FACTOR = 0.9
SKIPPED_TOOL_MESSAGE = "Tool call skipped: research budget exceeded."

# --- Terminal Execution Logging ---
EXECUTION_LOGGING_ENABLED = False
EXECUTION_LOG_MAX_CHARS = 1200
EXECUTION_LOG_USE_COLOR = True

# --- Text Splitter Configuration ---
CHILD_CHUNK_SIZE = 500
CHILD_CHUNK_OVERLAP = 100
MIN_PARENT_SIZE = 2000
MAX_PARENT_SIZE = 4000
HEADERS_TO_SPLIT_ON = [
    ("#", "H1"),
    ("##", "H2"),
    ("###", "H3")
]

# --- Trace ---
TRACE_ENABLED = os.environ.get("TRACE_ENABLED", "false").lower() == "true"
TRACE_DIR = os.path.join(_BASE_DIR, "evals", "results", "traces")

# --- Langfuse Observability ---
LANGFUSE_ENABLED = os.environ.get("LANGFUSE_ENABLED", "false").lower() == "true"
LANGFUSE_PUBLIC_KEY = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.environ.get("LANGFUSE_SECRET_KEY", "")
LANGFUSE_BASE_URL = os.environ.get("LANGFUSE_BASE_URL", "http://localhost:3000")
