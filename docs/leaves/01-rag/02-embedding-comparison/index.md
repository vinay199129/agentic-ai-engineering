!!! info "`01-rag/02-embedding-comparison`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/your-handle/agentic-ai-engineering/tree/main/01-rag/02-embedding-comparison)

**Headline metrics:** _no headline metric_

# Embedding comparison

**Problem:** Different embedders rank the same query/document pair very differently. Picking blindly can cost you 10+ points of recall@k.

**What you'll learn:**
- How to set up a tiny apples-to-apples bench: same corpus, same queries, swap only the embedder.
- recall@{1, 3, 5} per configuration as the simplest decision metric.
- The role of dimensionality — higher isn't always better; cost and latency matter.
- Why hash-based "fake" embedders are useful for offline tests but never for production.
- Forward reference to `04-reranking/` for the second-stage cleanup most pipelines need.

**When to use it:** Any time you're choosing or replacing an embedding model in a RAG system.

**When NOT to use it:** Before you have any retrieval traffic — pick a sensible default (text-embedding-3-small or bge-small-en-v1.5) and measure once you have real queries.

## Run it

```powershell
uv sync --group rag
uv run jupyter lab 01-rag/02-embedding-comparison/notebook.ipynb
uv run python 01-rag/02-embedding-comparison/eval.py
```

The notebook uses the deterministic hashing embedder with different seeds + dimensions to simulate multiple "providers" entirely offline. Swap `shared.embedders.hash_embed` for `shared.llm.embed(...)` for real providers.

## Key results

See [`eval-snapshot.json`](https://github.com/your-handle/agentic-ai-engineering/blob/main/01-rag/02-embedding-comparison/./eval-snapshot.json) for per-configuration recall@k.

## References

- [MTEB leaderboard](https://huggingface.co/spaces/mteb/leaderboard) — start here before picking anything.
- Muennighoff et al., [MTEB: Massive Text Embedding Benchmark](https://arxiv.org/abs/2210.07316)
- Nussbaum et al., [Nomic Embed: Training a Reproducible Long Context Text Embedder](https://arxiv.org/abs/2402.01613)
