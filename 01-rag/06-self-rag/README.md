# Self-RAG — let the model decide whether to use each retrieval

**Problem:** Naive RAG stuffs the top-k chunks into the prompt and hopes for the best. The model has no way to say "this chunk is irrelevant" or "I can't actually support this answer".

**What you'll learn:**
- A two-stage prompt: per-chunk **relevance grader** + **support-aware answerer**.
- How a per-chunk `yes/no` filter cuts noise *before* the answer call (lower cost, higher precision).
- Why a `SUPPORT: yes/no` postscript is the cheapest hallucination tripwire you can add.
- The pattern that scales: replace the LLM grader with a fine-tuned classifier when volume justifies it.

Based on Asai et al., [Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection](https://arxiv.org/abs/2310.11511).

**When to use it:** RAG pipelines where wrong-doc hallucination is the dominant failure mode and you can spend ~k+1 extra LLM calls per query.

**When NOT to use it:** Latency-critical paths (this adds k+1 round-trips). Use a reranker (`04-reranking/`) first; only escalate to self-RAG if hallucination persists.

## Run it

```powershell
uv sync --group rag
uv run jupyter lab 01-rag/06-self-rag/notebook.ipynb
uv run python 01-rag/06-self-rag/eval.py
```

## Key results

See [`eval-snapshot.json`](./eval-snapshot.json) — compares refusal rate and answer-doc precision against naive RAG.

## References

- Asai et al., [Self-RAG](https://arxiv.org/abs/2310.11511)
- Anthropic, [Reducing hallucinations](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/reduce-hallucinations)
