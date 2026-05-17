!!! info "`02-indexing/06-colbert-late-interaction`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/vinay199129/agentic-ai-engineering/tree/main/02-indexing/06-colbert-late-interaction)

**Headline metrics:** _no headline metric_

# ColBERT-style late interaction — MaxSim over token embeddings

**Problem:** Single-vector dense retrieval collapses an entire document to one embedding. Subtle term matches get washed out — especially for queries that ask about specific entities buried in a long abstract. ColBERT keeps a vector *per token* and scores a (query, doc) pair by **MaxSim**: each query token picks its best-matching doc token and the scores are summed.

**What you'll learn:**
- The MaxSim scoring formula: `score(Q, D) = Σ_{q ∈ Q} max_{d ∈ D} sim(q, d)`.
- Why per-token embeddings beat sentence-level embeddings on entity-heavy queries.
- A scratch implementation over the shared hash embedder (one vector per token) that demonstrates the pattern in 40 lines — no GPU, no PLAID, no RAGatouille.
- The latency / memory cost: `|tokens|` more vectors and `O(|Q| · |D|)` more compute per scoring.

**When to use it:** Heterogeneous queries where some terms are entity-exact and others are paraphrase — late interaction handles both without an explicit fusion step. Production ColBERT (via [PLAID](https://github.com/stanford-futuredata/ColBERT/blob/main/docs/index.rst) or [RAGatouille](https://github.com/AnswerDotAI/RAGatouille)) competes with cross-encoder rerankers at a fraction of the latency.

**When NOT to use it:** Tight RAM / index-size budgets — late-interaction indexes are typically 6–10× larger than single-vector. Workloads dominated by global semantic similarity (pure paraphrase) where MaxSim adds no signal over a good bi-encoder.

## Run it

```powershell
uv sync --group indexing
uv run jupyter lab 02-indexing/06-colbert-late-interaction/notebook.ipynb
uv run python 02-indexing/06-colbert-late-interaction/eval.py
```

No LLM calls.

## Key results

See [`eval-snapshot.json`](https://github.com/vinay199129/agentic-ai-engineering/blob/main/02-indexing/06-colbert-late-interaction/./eval-snapshot.json) for `recall@{1,3,5}` of single-vector dense vs. late-interaction MaxSim plus the index size ratio (number of vectors stored).

## References

- Khattab & Zaharia, [ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction over BERT](https://arxiv.org/abs/2004.12832)
- Santhanam et al., [PLAID: An Efficient Engine for Late Interaction Retrieval](https://arxiv.org/abs/2205.09707)
- [RAGatouille](https://github.com/AnswerDotAI/RAGatouille) — practical late-interaction Python wrapper.
