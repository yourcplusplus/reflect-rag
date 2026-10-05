import uuid
from langchain_deepseek import ChatDeepSeek
import config
from db.vector_db_manager import VectorDbManager
from db.parent_store_manager import ParentStoreManager
from document_chunker import DocumentChunker
from rag_agent.tools import ToolFactory
from rag_agent.graph import create_agent_graph
from core.observability import Observability

class RAGSystem:

    def __init__(self, collection_name=config.CHILD_COLLECTION):
        self.collection_name = collection_name
        self.vector_db = VectorDbManager()
        self.parent_store = ParentStoreManager()
        self.chunker = DocumentChunker()
        self.observability = Observability()
        self.agent_graph = None
        self.thread_id = str(uuid.uuid4())
        self.recursion_limit = config.GRAPH_RECURSION_LIMIT

    def initialize(self):
        self.vector_db.create_collection(self.collection_name)
        collection = self.vector_db.get_collection(self.collection_name)
        dense_collection = self.vector_db.get_dense_collection(self.collection_name)

        if not config.DEEPSEEK_API_KEY:
            print("⚠️  DEEPSEEK_API_KEY is not set — chat will fail until you export it "
                  "(e.g. in project/.env or your shell).")

        # ChatDeepSeek requires a non-empty api_key to construct its client;
        # use a placeholder so the UI can start before DEEPSEEK_API_KEY is set.
        llm = ChatDeepSeek(
            model=config.LLM_MODEL,
            api_key=config.DEEPSEEK_API_KEY or "EMPTY",
            api_base=config.DEEPSEEK_BASE_URL,
            temperature=config.LLM_TEMPERATURE,
            request_timeout=60,   # fail fast on network stalls instead of freezing the UI for minutes
        )
        tools = ToolFactory(collection).create_tools()
        self.agent_graph = create_agent_graph(llm, tools, dense_collection=dense_collection)

    def get_config(self):
        cfg = {"configurable": {"thread_id": self.thread_id}, "recursion_limit": self.recursion_limit}
        handler = self.observability.get_handler()
        if handler:
            cfg["callbacks"] = [handler]
        return cfg

    def reset_thread(self):
        try:
            self.agent_graph.checkpointer.delete_thread(self.thread_id)
        except Exception as e:
            print(f"Warning: Could not delete thread {self.thread_id}: {e}")
        self.thread_id = str(uuid.uuid4())
