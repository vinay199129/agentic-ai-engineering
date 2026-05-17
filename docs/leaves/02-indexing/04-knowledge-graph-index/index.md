!!! info "`02-indexing/04-knowledge-graph-index`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/your-handle/agentic-ai-engineering/tree/main/02-indexing/04-knowledge-graph-index)

**Headline metrics:** _no headline metric_

# Knowledge-graph index — SPO triples + graph traversal

**Problem:** Vector search tells you *which documents are relevant*. It doesn't tell you *how entities relate*. Questions like "how does AdaSpec relate to Llama-3 70B?" need multi-hop reasoning over typed relations, not nearest neighbours.

**What you'll learn:**
- Extract `(subject, predicate, object)` triples from a corpus with one LLM call per document.
- Build a `networkx.DiGraph` over the triples.
- Answer multi-hop questions via `shortest_path` + a tiny synthesis LLM call.
- The complementarity between vector retrieval (document-level) and KG retrieval (entity-level).

**When to use it:** Multi-hop / relational queries; compliance & auditing where you need to *show your work*; corpora where the unit of interest is an entity, not a paragraph (org charts, product catalogues, regulations).

**When NOT to use it:** Single-document factual lookups (regular RAG is cheaper and more accurate). Unstructured social-text corpora where triples don't naturally exist.

## Run it

```powershell
uv sync --group indexing
uv run jupyter lab 02-indexing/04-knowledge-graph-index/notebook.ipynb
uv run python 02-indexing/04-knowledge-graph-index/eval.py
```

The notebook uses cached LLM responses (`LLM_CACHE_ONLY=1`) by default so it runs without an API key. The eval is fully deterministic — it reads triples from the cache and reports graph structural metrics without making any new LLM calls.

## Key results

See [`eval-snapshot.json`](https://github.com/your-handle/agentic-ai-engineering/blob/main/02-indexing/04-knowledge-graph-index/./eval-snapshot.json) for: nodes / edges / average degree of the extracted graph, plus a *connectivity* metric — fraction of multi-hop questions for which `nx.shortest_path` reaches the named target entity.

## References

- Microsoft Research, [GraphRAG: Unlocking LLM discovery on narrative private data](https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/)
- [LlamaIndex `KnowledgeGraphIndex`](https://docs.llamaindex.ai/en/stable/examples/index_structs/knowledge_graph/KnowledgeGraphDemo/)
- Neo4j, [The Neo4j RAG Playbook](https://neo4j.com/developer-blog/knowledge-graph-rag-application/)
- See also: `01-rag/09-graph-rag/` for the community-summary flavour of graph RAG.
