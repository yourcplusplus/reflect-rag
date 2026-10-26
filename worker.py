#!/usr/bin/env python3
"""Async document-ingestion worker (Redis List queue).

    python worker.py

Runs one consumer loop for ``doc:ingest:queue``: BRPOPLPUSH -> index -> ACK.
It is a *separate process* from the API on purpose:

* a worker crash never takes the HTTP API down (and vice versa);
* indexing loads BGE-M3 but not the LLM graph or the reranker, so its memory
  footprint is much smaller than the API's;
* one consumer serialises re-indexing of the same document ().

Qdrant must be a server (``QDRANT_URL``): the embedded local database takes an
exclusive file lock, so two processes cannot share it.

Configuration is the same as the API's (``project/.env`` + environment):
DATABASE_URL, REDIS_URL, QDRANT_URL, INGEST_MAX_ATTEMPTS, INGEST_STALE_SECONDS,
INGEST_POLL_TIMEOUT, ...
"""
from __future__ import annotations

import logging
import signal
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent
PROJECT_DIR = REPO_DIR / "project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

# api.settings loads project/.env before the RAG core is imported.
from api.settings import settings  # noqa: E402

logger = logging.getLogger("worker")


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )
    if not settings.qdrant_url:
        logger.error(
            "QDRANT_URL is required for the ingest worker: the embedded local Qdrant "
            "only allows one process. Start a Qdrant server (docker compose up -d qdrant) "
            "and set QDRANT_URL=http://<host>:6333."
        )
        return 2

    # The core builds QdrantClient(path=...) internally; this redirects it (and
    # every later client this process creates) to the configured server.
    from api import patches

    patches.install_qdrant_server_shim(settings.qdrant_url)

    from api.ingest.consumer import IngestWorker

    worker = IngestWorker()
    # Graceful shutdown: finish the current document, then exit. A hard kill is
    # also safe — the id stays in `processing` and is recovered on next start.
    signal.signal(signal.SIGTERM, lambda *_: worker.stop())
    signal.signal(signal.SIGINT, lambda *_: worker.stop())

    logger.info(
        "worker starting: database=%s redis=%s qdrant=%s",
        settings.database_url.split("@")[-1],
        settings.redis_url,
        settings.qdrant_url,
    )
    worker.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
