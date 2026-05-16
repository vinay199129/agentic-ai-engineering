# 02 — Indexing

Vector DB comparison plus deep dives into the algorithms underneath the embeddings.

## Planned leaves

| Leaf | Topic | Status |
|---|---|---|
| `00-vector-db-comparison/` | pgvector, Qdrant, Chroma, LanceDB, Weaviate, Milvus — matrix + benchmark (recall@10, p95 latency, $/1M vectors) | ⏳ Phase 3 |
| `01-hnsw-deep-dive/` | Build HNSW from scratch in numpy; visualize layered graph | ⏳ Phase 3 |
| `02-ivf-pq-quantization/` | FAISS IVF-PQ; recall vs. memory tradeoff | ⏳ Phase 3 |
| `03-bm25-and-hybrid/` | `rank_bm25` + dense fusion (RRF, weighted) | ⏳ Phase 3 |
| `04-knowledge-graph-index/` | Neo4j + LlamaIndex KG indexer | ⏳ Phase 3 |
| `05-summary-tree-index/` | LlamaIndex hierarchical summarization | ⏳ Phase 3 |
| `06-colbert-late-interaction/` | PLAID / RAGatouille | ⏳ Phase 3 |
| `07-incremental-indexing/` | Delta indexing, deletes, re-embed strategies | ⏳ Phase 3 |
