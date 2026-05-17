!!! info "`01-rag/11-long-context-rag`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/your-handle/agentic-ai-engineering/tree/main/01-rag/11-long-context-rag)

**Headline metrics:** _no headline metric_

# Long-context RAG — Anthropic contextual retrieval

**Problem:** When a long document is chunked, each chunk loses its surrounding context. The retriever sees an orphan paragraph with no idea which paper it came from. Recall suffers.

**What you'll learn:**
- **Contextual retrieval** (Anthropic, 2024): one extra cheap LLM call per chunk to generate a short "where this chunk sits" prefix.
- Prepend the prefix → re-embed → compare recall.
- Why this stacks additively with hybrid search and reranking.
- Cost mitigation via Anthropic prompt caching on the document portion.

Based on Anthropic, [Introducing Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval).

**When to use it:** Long-document corpora where each chunk is ambiguous without its parent context — research papers, codebases, transcripts.

**When NOT to use it:** Already-short documents (FAQ items, tweets). The prefix is redundant.

## Run it

```powershell
uv sync --group rag
uv run jupyter lab 01-rag/11-long-context-rag/notebook.ipynb
uv run python 01-rag/11-long-context-rag/eval.py
```

## Key results

See [`eval-snapshot.json`](https://github.com/your-handle/agentic-ai-engineering/blob/main/01-rag/11-long-context-rag/./eval-snapshot.json) for recall@{1,3,5} bare vs contextualized chunks on a 5-doc subset.

## References

- Anthropic, [Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)
- [Anthropic prompt caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)
