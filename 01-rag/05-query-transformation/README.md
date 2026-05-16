# Query transformation

**Problem:** Sometimes the user's literal question is a *bad embedding query*. The corpus vocabulary doesn't match the question vocabulary, or the question is too specific, or it requires joining facts across documents.

**What you'll learn:**
- **HyDE** — generate a hypothetical answer and embed *that* for retrieval. The answer's vocabulary aligns with the corpus.
- **Multi-query** — generate N paraphrases, retrieve for each, union the results. Cheap recall boost.
- **Step-back** — generalize the question before retrieving; useful for concept-level corpora.
- **Decomposition** — split multi-hop questions into atomic sub-questions, retrieve for each, recombine.
- When each transformation hurts more than it helps (e.g., HyDE on entity-heavy queries).

**When to use it:** Any RAG system where retrieval is the bottleneck — measure first with `00-naive-rag/eval.py` and see whether `context_recall` is dragging the answer metric down.

**When NOT to use it:** When retrieval is already at ceiling. Each transformation adds at least one LLM call.

## Run it

```powershell
uv sync --group rag
uv run jupyter lab 01-rag/05-query-transformation/notebook.ipynb
uv run python 01-rag/05-query-transformation/eval.py
```

## Key results

See [`eval-snapshot.json`](./eval-snapshot.json) for recall@{1,3} per transformation strategy on the answerable subset of the golden Q&A.

## References

- Gao et al., [Precise Zero-Shot Dense Retrieval without Relevance Labels (HyDE)](https://arxiv.org/abs/2212.10496)
- Zheng et al., [Take a Step Back: Evoking Reasoning via Abstraction in Large Language Models](https://arxiv.org/abs/2310.06117)
- [LangChain MultiQueryRetriever](https://python.langchain.com/docs/how_to/MultiQueryRetriever/)
