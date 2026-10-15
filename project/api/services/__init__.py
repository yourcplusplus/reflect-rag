"""Service layer: the API's adapters around the RAG core."""

from api.services.rag_service import RagService, iter_blocking

__all__ = ["RagService", "iter_blocking"]
