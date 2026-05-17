!!! info "`01-rag/04-reranking`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/your-handle/agentic-ai-engineering/tree/main/01-rag/04-reranking)

**Headline metrics:** _no headline metric_

# Reranking — cleanup pass over first-stage retrieval

**Problem:** First-stage retrievers (dense, BM25, hybrid) are tuned for recall and dump barely-relevant chunks into the top-20. A second-stage **reranker** re-orders that candidate set with a stronger (slower, costlier) model so the top-3 is actually correct.

**What you'll learn:**
- **Cross-encoder reranking** (BGE / Cohere Rerank pattern) — the production default. Implemented here as a token-overlap stand-in; the interface matches `sentence_transformers.CrossEncoder.predict`.
- **LLM-as-reranker** — zero-shot prompt that picks the most relevant id; expensive but no training and policy-flexible.
- Why fetching k=50 with hybrid and reranking to top-3 beats fetching k=3 with anything alone.
- A recall@1 sweep: no rerank vs cross-encoder vs LLM-as-reranker.

**When to use it:** Anytime first-stage recall is fine but precision@k is the bottleneck — usually true for k <= 5. Almost always worth the latency on RAG that feeds an LLM.

**When NOT to use it:** When first-stage already has the right doc at rank 1 (test this — many small corpora do). When budget for an extra inference per query is hard-capped.

## Run it

```powershell
uv sync --group rag
uv run jupyter lab 01-rag/04-reranking/notebook.ipynb
uv run python 01-rag/04-reranking/eval.py
```

## Key results

See [`eval-snapshot.json`](https://github.com/your-handle/agentic-ai-engineering/blob/main/01-rag/04-reranking/./eval-snapshot.json) for recall@1 pre / post each reranker.

## References

- Nogueira & Cho, [Passage Re-ranking with BERT](https://arxiv.org/abs/1901.04085)
- [BGE Reranker (bge-reranker-base)](https://huggingface.co/BAAI/bge-reranker-base)
- [Cohere Rerank v3 docs](https://docs.cohere.com/docs/rerank)
- Sun et al., [Is ChatGPT Good at Search? Investigating LLMs as Re-Ranking Agents](https://arxiv.org/abs/2304.09542)
