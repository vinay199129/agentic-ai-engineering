!!! info "`01-rag/03-hybrid-search`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/vinay199129/agentic-ai-engineering/tree/main/01-rag/03-hybrid-search)

**Headline metrics:** _no headline metric_

# Hybrid search — BM25 + dense + RRF fusion

**Problem:** Dense retrieval misses exact entity / acronym matches. BM25 misses paraphrase. Most real corpora need both.

**What you'll learn:**
- Building a sparse (BM25 via `rank_bm25`) index in 3 lines.
- Building a dense index with the shared hashing embedder (swap for any real provider).
- **Reciprocal Rank Fusion (RRF)** — the parameter-free combiner that almost always beats either retriever alone.
- A side-by-side recall@{1,3,5} sweep on the golden Q&A.

**When to use it:** Any corpus with proper nouns, IDs, acronyms, or mixed query styles (some terse, some natural language). Hybrid is the right *default* — it's strictly better than dense-only on heterogeneous corpora.

**When NOT to use it:** Pure-paraphrase corpora where BM25 only adds noise. Or when retrieval is dominated by reranker quality (see `04-reranking/`).

## Run it

```powershell
uv sync --group rag
uv run jupyter lab 01-rag/03-hybrid-search/notebook.ipynb
uv run python 01-rag/03-hybrid-search/eval.py
```

No LLM calls; runs anywhere.

## Key results

See [`eval-snapshot.json`](https://github.com/vinay199129/agentic-ai-engineering/blob/main/01-rag/03-hybrid-search/./eval-snapshot.json) for per-retriever recall@{1,3,5}. Compare against [`../00-naive-rag/eval-snapshot.json`](https://github.com/vinay199129/agentic-ai-engineering/blob/main/01-rag/03-hybrid-search/../00-naive-rag/eval-snapshot.json) for the dense-only baseline.

## References

- Cormack et al., [Reciprocal Rank Fusion outperforms Condorcet and individual rank learning methods](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
- Robertson & Zaragoza, [The Probabilistic Relevance Framework: BM25 and Beyond](https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf)
- [Weaviate hybrid search docs](https://weaviate.io/developers/weaviate/search/hybrid)
