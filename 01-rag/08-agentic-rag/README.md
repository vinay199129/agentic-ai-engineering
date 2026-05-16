# Agentic RAG — let the model pick the retrieval strategy

**Problem:** Naive RAG always runs a vector search, even when the user asked for a specific doc by id, or when the question needs no retrieval at all ("what does RAG stand for?"). That wastes calls and degrades answers.

**What you'll learn:**
- A minimal **tool-calling router** with three tools: `search_papers`, `lookup_doc`, `answer_directly`.
- The single-step agent loop: model picks tool → we execute → feed result back → model answers.
- How agentic RAG composes the lessons from `00-foundations/02-function-calling/` and `00-foundations/04-prompt-patterns/`.
- The tradeoff: routing latency vs answer quality on heterogeneous query mixes.

**When to use it:** Heterogeneous query traffic — mix of search-style, doc-lookup, and chit-chat queries. The router pays for itself by skipping retrieval when it's noise.

**When NOT to use it:** Homogeneous query distributions where vector search is almost always the right answer. Routing overhead isn't worth it.

## Run it

```powershell
uv sync --group rag
uv run jupyter lab 01-rag/08-agentic-rag/notebook.ipynb
uv run python 01-rag/08-agentic-rag/eval.py
```

## Key results

See [`eval-snapshot.json`](./eval-snapshot.json) — per-route counts on three example queries.

## References

- Anthropic, [Building effective agents](https://www.anthropic.com/research/building-effective-agents)
- [OpenAI function calling docs](https://platform.openai.com/docs/guides/function-calling)
- [LangGraph agentic RAG tutorial](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_agentic_rag/)
