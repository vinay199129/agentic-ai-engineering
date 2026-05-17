!!! info "`01-rag/00-naive-rag`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/vinay199129/agentic-ai-engineering/tree/main/01-rag/00-naive-rag)

**Headline metrics:** `context_recall`=0.75 · `answer_exact_match_direct`=0.955

# Naive RAG — chunk · embed · top-k · stuff

**Problem:** The simplest possible retrieval-augmented pipeline. Every other technique in `01-rag/` is measured against this baseline.

**What you'll learn:**
- Indexing a small arxiv corpus with a deterministic embedder (so the notebook runs offline in CI).
- Top-k retrieval via cosine similarity — and how to swap in a real provider's embedder behind the same interface.
- The "stuff" pattern — concatenate top-k chunks into a single prompt.
- Three evaluation metrics that catch the most common failure modes: `context_recall`, `refusal_rate_on_unanswerable`, `answer_exact_match_direct`.
- Why naive RAG fails on multi-hop, long-context, and near-duplicate corpora (forward references to chunking, hybrid search, reranking).

**When to use it:** Always — as your baseline. Don't ship anything fancier until you've measured against this.

**When NOT to use it (in production):** Multi-hop questions, near-duplicate chunks, queries where lexical match beats semantic match (think exact entity names).

## Run it

```powershell
uv sync --group rag
uv run jupyter lab 01-rag/00-naive-rag/notebook.ipynb
uv run python 01-rag/00-naive-rag/eval.py
```

## Key results

See [`eval-snapshot.json`](https://github.com/vinay199129/agentic-ai-engineering/blob/main/01-rag/00-naive-rag/./eval-snapshot.json) for the latest numbers. The bench is small (30 hand-curated Q&A over 10 synthetic abstracts) — small enough to be deterministic, big enough to show the next technique helping.

## References

- Lewis et al., [RAG: Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401)
- Karpukhin et al., [Dense Passage Retrieval for Open-Domain QA](https://arxiv.org/abs/2004.04906)
- [LlamaIndex naive RAG tutorial](https://docs.llamaindex.ai/en/stable/getting_started/starter_example/)
