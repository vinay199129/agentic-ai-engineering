# Corrective RAG (CRAG)

**Problem:** Sometimes the corpus simply doesn't contain the answer. Self-RAG can detect *which* chunks are good but can't fix the case where *all* of them are bad. CRAG adds a routing step that escalates to an external source.

**What you'll learn:**
- A retrieval-quality **grader** that classifies the retrieved set as `confident` / `ambiguous` / `insufficient`.
- A three-way **router**: corpus-only / corpus+web / web-only.
- How even a mocked web fallback dramatically improves refusal behaviour on out-of-corpus questions.
- Why CRAG composes nicely with `06-self-rag/` — same grader can drive both per-chunk filtering and outer routing.

Based on Yan et al., [Corrective Retrieval Augmented Generation](https://arxiv.org/abs/2401.15884).

**When to use it:** Production RAG over a finite corpus where users routinely ask questions outside it. The router is the cheapest way to add a meaningful "I don't know, but here's what the web says" path.

**When NOT to use it:** Closed-domain assistants where escaping the corpus is a *policy violation* — there you want a hard refusal, not a fallback.

## Run it

```powershell
uv sync --group rag
uv run jupyter lab 01-rag/07-corrective-rag/notebook.ipynb
uv run python 01-rag/07-corrective-rag/eval.py
```

The notebook uses a mocked web tool — swap in Tavily / Bing / Brave for real use.

## Key results

See [`eval-snapshot.json`](./eval-snapshot.json) for per-verdict accuracy on the answerable + unanswerable subsets.

## References

- Yan et al., [CRAG](https://arxiv.org/abs/2401.15884)
- [Tavily Search API](https://tavily.com/)
