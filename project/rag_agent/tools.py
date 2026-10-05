import time

from FlagEmbedding import FlagReranker
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
import config
from core.trace import collector_from_config
from db.parent_store_manager import ParentStoreManager
from core.execution_logger import log_error, log_tool_end, log_tool_start

class ToolFactory:

    def __init__(self, collection):
        self.collection = collection
        self.parent_store_manager = ParentStoreManager()
        self.reranker = FlagReranker(config.RERANKER_MODEL, use_fp16=True) if config.ENABLE_RERANKER else None

    def _rerank(self, query, scored_docs, run_config: RunnableConfig = None):
        """Return docs ordered by reranker score (descending).

        Emits the retrieval candidates (vector order + fused scores) and the
        post-rerank ordering to the request trace when one is attached.
        Falls back to the original vector-search order if the reranker fails,
        so retrieval keeps working without reranking.
        """
        entries = []
        for rank, (doc, fused_score) in enumerate(scored_docs):
            entries.append({
                "rank": rank,
                "point_id": doc.metadata.get("_id") or f"noid_{rank}",
                "parent_id": doc.metadata.get("parent_id", ""),
                "source": doc.metadata.get("source", ""),
                "fused_score": fused_score,
                "preview": str(doc.page_content)[:250],
                "doc": doc,
            })
        if collector := collector_from_config(run_config):
            collector.emit("retrieval", "candidates", {
                "query": query,
                "mode": self._retrieval_mode_name(),
                "count": len(entries),
                "candidates": [{k: v for k, v in entry.items() if k != "doc"} for entry in entries],
            })

        if not config.ENABLE_RERANKER:
            # Ablation variant: no reranker — keep the vector-search order and
            # skip the reranked event entirely (no scoring happened).
            return [entry["doc"] for entry in entries]

        try:
            t0 = time.perf_counter()
            scores = self.reranker.compute_score(
                [(query, entry["doc"].page_content) for entry in entries], batch_size=4
            )
            if not isinstance(scores, list):
                scores = [scores]
            latency_ms = (time.perf_counter() - t0) * 1000
            for entry, score in zip(entries, scores):
                entry["rerank_score"] = float(score)
        except Exception as e:
            log_error("search_child_chunks/rerank", e)
            return [entry["doc"] for entry in entries]

        ordered = sorted(entries, key=lambda entry: entry["rerank_score"], reverse=True)
        if collector:
            pre_index = {entry["point_id"]: i for i, entry in enumerate(entries)}
            post_rank = [entry["point_id"] for entry in ordered]
            collector.emit("rerank", "reranked", {
                "pre_rank": [entry["point_id"] for entry in entries],
                "post_rank": post_rank,
                "rerank_scores": {entry["point_id"]: entry["rerank_score"] for entry in ordered},
                "moved_up": [pid for i, pid in enumerate(post_rank) if pre_index[pid] > i],
                "latency_ms": round(latency_ms),
            })
        return [entry["doc"] for entry in ordered]

    def _retrieval_mode_name(self):
        mode = getattr(self.collection, "retrieval_mode", None)
        value = getattr(mode, "value", None) or getattr(mode, "name", "")
        return str(value).lower() or "hybrid"

    def _search_child_chunks(self, query: str, limit: int = config.DEFAULT_RETRIEVAL_K, run_config: RunnableConfig = None) -> str:
        """Search document excerpts for evidence related to the user question.

        Use this as the first retrieval step. Results include parent IDs, file
        names, and short child-chunk excerpts. If excerpts are relevant but too
        fragmented to answer confidently, call retrieve_parent_chunks with the
        returned parent_id.

        Args:
            query: Focused search query with concrete keywords from the question.
            limit: Maximum number of child chunks to return.
        """
        log_tool_start("search_child_chunks", {"query": query, "limit": limit})
        try:
            recall_k = limit * config.RERANKER_TOP_K_MULTIPLIER
            scored_docs = self.collection.similarity_search_with_score(
                query,
                k=recall_k,
                score_threshold=config.RETRIEVAL_SCORE_THRESHOLD,
            )
            if not scored_docs:
                output = "NO_RELEVANT_CHUNKS"
                log_tool_end("search_child_chunks", output)
                return output

            results = self._rerank(query, scored_docs, run_config=run_config)[:limit]

            output = config.CHILD_CHUNK_SEPARATOR.join([
                f"Parent ID: {doc.metadata.get('parent_id', '')}\n"
                f"File Name: {doc.metadata.get('source', '')}\n"
                f"Content: {doc.page_content.strip()}"
                for doc in results
            ])
            log_tool_end("search_child_chunks", output)
            return output

        except Exception as e:
            log_error("search_child_chunks", e)
            output = f"RETRIEVAL_ERROR: {str(e)}"
            log_tool_end("search_child_chunks", output)
            return output
    
    def _retrieve_parent_chunks(self, parent_id: str) -> str:
        """Retrieve the full parent chunk for a relevant child search result.

        Use this only after search_child_chunks returns a relevant parent_id and
        the child excerpt needs more surrounding context. Do not call this for
        parent IDs already available in compressed context.
    
        Args:
            parent_id: Parent chunk ID returned by search_child_chunks.
        """
        log_tool_start("retrieve_parent_chunks", {"parent_id": parent_id})
        try:
            parent = self.parent_store_manager.load_content(parent_id)
            if not parent:
                output = "NO_PARENT_DOCUMENT"
                log_tool_end("retrieve_parent_chunks", output)
                return output

            output = (
                f"Parent ID: {parent.get('parent_id', 'n/a')}\n"
                f"File Name: {parent.get('metadata', {}).get('source', 'unknown')}\n"
                f"Content: {parent.get('content', '').strip()}"
            )
            log_tool_end("retrieve_parent_chunks", output)
            return output

        except Exception as e:
            log_error("retrieve_parent_chunks", e)
            output = f"PARENT_RETRIEVAL_ERROR: {str(e)}"
            log_tool_end("retrieve_parent_chunks", output)
            return output
    
    def create_tools(self) -> list:
        """Create and return the list of tools."""
        search_tool = tool("search_child_chunks")(self._search_child_chunks)
        retrieve_tool = tool("retrieve_parent_chunks")(self._retrieve_parent_chunks)
        
        return [search_tool, retrieve_tool]
