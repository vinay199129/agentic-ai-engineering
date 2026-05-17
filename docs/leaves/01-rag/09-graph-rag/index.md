!!! info "`01-rag/09-graph-rag`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/vinay199129/agentic-ai-engineering/tree/main/01-rag/09-graph-rag)

**Headline metrics:** _no headline metric_

# Graph RAG — entity-centric retrieval over a knowledge graph

**Problem:** Question answering over a corpus often needs *concepts*, not just text matches. "What inference-speedup techniques are in the corpus?" is hard to answer by retrieving one chunk at a time — you need to enumerate a *cluster* of related work.

**What you'll learn:**
- LLM-driven **entity extraction** per document (one cheap call per doc, cached).
- Build a co-mention graph in `networkx`: nodes = entities, edges = co-occur in same paper.
- **Community detection** via greedy modularity; each community is a topical cluster.
- LLM-generated **community summaries** that answer concept-level questions in one shot.
- The split between **local** retrieval (entity neighbourhood) and **global** retrieval (community summary).

Based on Edge et al. (Microsoft), [From Local to Global: A Graph RAG Approach to Query-Focused Summarization](https://arxiv.org/abs/2404.16130).

**When to use it:** Concept-level Q&A over a corpus where the corpus has natural topic clusters (research papers, support tickets, case law).

**When NOT to use it:** Fact-lookup or exact-quote retrieval — vanilla RAG is faster and more precise.

## Run it

```powershell
uv sync --group rag
uv run jupyter lab 01-rag/09-graph-rag/notebook.ipynb
uv run python 01-rag/09-graph-rag/eval.py
```

## Key results

See [`eval-snapshot.json`](https://github.com/vinay199129/agentic-ai-engineering/blob/main/01-rag/09-graph-rag/./eval-snapshot.json) — counts entities, edges, communities, and how many docs each community spans.

## References

- Edge et al., [Graph RAG (Microsoft)](https://arxiv.org/abs/2404.16130)
- [networkx community algorithms](https://networkx.org/documentation/stable/reference/algorithms/community.html)
- [LightRAG](https://github.com/HKUDS/LightRAG)
