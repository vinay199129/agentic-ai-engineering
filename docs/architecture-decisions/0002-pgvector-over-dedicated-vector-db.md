# 0002 — Use `pgvector` instead of a dedicated vector DB

- **Status:** accepted
- **Date:** 2025-11-08
- **Context:** The deep-dive repo `production-rag-pipeline` needs a
  production-grade vector store, plus a metadata store, plus
  HITL-checkpoint storage. The conventional move is to add a dedicated
  vector DB (Qdrant / Pinecone / Weaviate) *alongside* Postgres. We
  weighed the cost of operating two stateful services against the
  cost of leaning harder on Postgres.
- **Decision:** Use **Postgres + `pgvector`** as the single source of
  truth for vectors, document metadata, agent state, and checkpoints.
  The Phase 8 [`docker-compose-stack`](../leaves/07-deployment-patterns/02-docker-compose-stack/index.md)
  leaf demonstrates the topology.
- **Consequences:**
  - **Good** — One backup story, one ops story, one connection-pool
    story. Transactions can span vector inserts and metadata updates,
    which makes the indexer code dramatically simpler. The
    `pgvector` HNSW implementation has caught up enough that for
    < 10 M vectors it is competitive with dedicated stores.
  - **Bad** — At very large scale (10 M+ vectors, > 100 QPS), a
    purpose-built store will outperform Postgres. We accept that we
    will have to migrate at that point, and we accept a clean
    abstraction layer over the store so the migration is mechanical.
  - **Bad** — `pgvector` HNSW build cost is non-trivial; we mitigate
    with partial indexes and overnight `REINDEX`.
- **Alternatives considered:**
  - **Qdrant** — Excellent product; would have been our choice if the
    HITL checkpoint story required a different data model. It doesn't.
  - **Pinecone** — Cleanest hosted experience, but the cost curve is
    aggressive and we wanted everything reproducible inside a single
    `docker compose up`.
  - **Weaviate** — Strong on the schema side; lost on operational
    simplicity vs. Postgres-we-already-run.
