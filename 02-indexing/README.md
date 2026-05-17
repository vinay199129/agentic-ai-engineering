# 02 — Indexing

Vector DB comparison plus deep dives into the algorithms underneath the embeddings.

## Planned leaves

| Leaf | Topic | Status |
|---|---|---|
| `00-vector-db-comparison/` | Flat / scratch-HNSW / IVF / BM25 — recall@{1,3,5} + build_ms matrix on the canonical Q&A | ✅ Phase 3 |
| `01-hnsw-deep-dive/` | Pure-numpy HNSW (Malkov & Yashunin 2016) with an `ef_search` sweep + layered-graph visualisation | ✅ Phase 3 |
| `02-ivf-pq-quantization/` | IVF nprobe sweep + PQ approx scoring + memory-ratio analysis | ✅ Phase 3 |
| `03-bm25-and-hybrid/` | BM25 internals (k1, b), TF-IDF baseline, RRF, weighted-α fusion sweep | ✅ Phase 3 |
| `04-knowledge-graph-index/` | LLM-extracted SPO triples → `networkx.DiGraph` → multi-hop coverage / connectivity | ✅ Phase 3 |
| `05-summary-tree-index/` | Leaf-summary embedding → k-means clusters → tree-route vs flat retrieve recall | ✅ Phase 3 |
| `06-colbert-late-interaction/` | Per-token embeddings + MaxSim from scratch; recall + index-size cost vs single-vector | ✅ Phase 3 |
| `07-incremental-indexing/` | Adds, tombstone deletes, re-embeds; demonstrates the mixed-embedder recall cliff | ✅ Phase 3 |

