!!! info "`01-rag/01-chunking-strategies`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/vinay199129/agentic-ai-engineering/tree/main/01-rag/01-chunking-strategies)

**Headline metrics:** _no headline metric_

# Chunking strategies

**Problem:** Chunking is the most underrated knob in RAG. The same corpus and the same retriever can swing recall@k by tens of points purely on how you split text.

**What you'll learn:**
- **Fixed-size** (character window with overlap) — fast, structure-blind.
- **Recursive** (paragraph → sentence → word boundaries) — the safe default.
- **Semantic** (split where adjacent-sentence embeddings diverge) — preserves topic boundaries.
- **Propositional** (atomic-claim extraction) — best recall, needs an LLM at index time.
- Side-by-side metrics on the canonical corpus: average chunk count, average chunk size, retrieval recall@3 for each strategy.

**When to use it:** Any RAG system whose documents are longer than ~500 characters. Always benchmark at least recursive vs. semantic on your corpus before locking in a strategy.

**When NOT to use it:** Corpora where each document is already shorter than the model's effective context window — one chunk per document is usually optimal.

## Run it

```powershell
uv sync --group rag
uv run jupyter lab 01-rag/01-chunking-strategies/notebook.ipynb
uv run python 01-rag/01-chunking-strategies/eval.py
```

The notebook uses no LLM calls — pure splitting + deterministic hash embeddings — so it runs anywhere.

## Key results

See [`eval-snapshot.json`](https://github.com/vinay199129/agentic-ai-engineering/blob/main/01-rag/01-chunking-strategies/./eval-snapshot.json) for chunk count / size / recall@3 per strategy.

## References

- LlamaIndex, [Chunking strategies](https://docs.llamaindex.ai/en/stable/optimizing/production_rag/)
- Greg Kamradt, [The 5 levels of text splitting](https://github.com/FullStackRetrieval-com/RetrievalTutorials/blob/main/tutorials/LevelsOfTextSplitting/5_Levels_Of_Text_Splitting.ipynb)
- Chen et al., [Dense X Retrieval: What Retrieval Granularity Should We Use?](https://arxiv.org/abs/2312.06648)
