# 01 — RAG

Every major RAG technique, evaluated on the same corpus so tradeoffs are comparable.

## Planned leaves

| Leaf | Technique | Status |
|---|---|---|
| `00-naive-rag/` | Chunk → embed → top-k → stuff | ⏳ Phase 1 |
| `01-chunking-strategies/` | Fixed, recursive, semantic, propositional, contextual (Anthropic) | ⏳ Phase 1 |
| `02-embedding-comparison/` | OpenAI, Cohere, BGE, Voyage, Nomic, mxbai | ⏳ Phase 1 |
| `03-hybrid-search/` | BM25 + dense + RRF fusion | ⏳ Phase 2 |
| `04-reranking/` | Cohere Rerank, BGE reranker, ColBERT late interaction | ⏳ Phase 2 |
| `05-query-transformation/` | HyDE, multi-query, step-back, decomposition | ⏳ Phase 2 |
| `06-self-rag/` | Self-reflection tokens / self-grading | ⏳ Phase 2 |
| `07-corrective-rag/` | CRAG: retrieval grader + web fallback | ⏳ Phase 2 |
| `08-agentic-rag/` | Router + tool-calling retrieval | ⏳ Phase 2 |
| `09-graph-rag/` | Microsoft GraphRAG: entity + community extraction | ⏳ Phase 2 |
| `10-multimodal-rag/` | Image + text via ColPali / Voyage Multimodal | ⏳ Phase 2 |
| `11-long-context-rag/` | Contextual retrieval (Anthropic) + cache-augmented | ⏳ Phase 2 |
| `12-comparison-bench/` | Side-by-side eval table on shared corpus, auto-generated from snapshots | ⏳ Phase 2 |

All leaves share the canonical corpus in `benchmarks/corpus/` and the golden Q&A set in `benchmarks/golden-qa/`.
