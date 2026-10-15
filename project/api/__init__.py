"""REST API service layer for ReflectRAG.

The package wraps the existing RAG core (``core``, ``rag_agent``, ``db``)
without modifying it: ``api.services.rag_service`` owns the single ``RAGSystem``
instance the same way ``ui/gradio_app.py`` does, and the routers add the
persistence and caching the Gradio app does not have.

Run it from the repository root with::

    uvicorn api.main:app --app-dir project

or, from ``project/``::

    uvicorn api.main:app
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
