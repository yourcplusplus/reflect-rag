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
CHILD_CHUNK_SEPARATOR = "\n\n<CHILD_CHUNK_BOUNDARY>\n\n"

# --- Agent Configuration ---
MAX_TOOL_CALLS = 8
MAX_ITERATIONS = 10
GRAPH_RECURSION_LIMIT = 50
MAIN_HISTORY_MESSAGES_TO_KEEP = 4
BASE_TOKEN_THRESHOLD = 2000
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
