| leaf | technique | headline metric | value |
| --- | --- | --- | --- |
| `00-naive-rag` | naive-rag | context_recall | 0.75 |
| `01-chunking-strategies` | chunking-strategies | avg chunks/doc (fixed) | 3.2 |
| `02-embedding-comparison` | embedding-comparison | recall@3 (large-512) | 0.9231 |
| `03-hybrid-search` | hybrid-search | recall@3 (hybrid RRF) | 0.9615 |
| `04-reranking` | reranking | recall@1 (LLM reranker) | 0.9615 |
| `05-query-transformation` | query-transformation | recall@3 (HyDE) | 0.7273 |
| `06-self-rag` | self-rag | refusal_rate (unanswerable) | 1.0 |
| `07-corrective-rag` | corrective-rag | verdict_accuracy | 1.0 |
| `08-agentic-rag` | agentic-rag | route_accuracy | 1.0 |
| `09-graph-rag` | graph-rag | n_communities | 6 |
| `10-multimodal-rag` | multimodal-rag | recall@3 (joint) | 0.8462 |
| `11-long-context-rag` | long-context-rag | recall@3 (contextual) | 0.8667 |
