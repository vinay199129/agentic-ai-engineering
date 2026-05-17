!!! info "`01-rag/12-comparison-bench`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/vinay199129/agentic-ai-engineering/tree/main/01-rag/12-comparison-bench)

**Headline metrics:** _no headline metric_

# Comparison bench — leaderboard across every `01-rag/` leaf

**Problem:** A repo full of RAG techniques is only useful if you can compare them. This leaf has no model of its own — it walks every sibling `eval-snapshot.json`, picks one headline metric per technique, and emits a Markdown table you can paste into a README.

**What it does:**
- Reads `01-rag/*/eval-snapshot.json`.
- Looks up each technique's headline metric in an explicit dispatch table (no fragile auto-discovery).
- Renders a leaderboard.
- Writes its own `eval-snapshot.json` so CI's regression-diff workflow can track it.

**When to use it:** As the final step when adding a new RAG leaf — register the headline metric in `HEADLINES` so it appears in the table.

## Run it

```powershell
uv run jupyter lab 01-rag/12-comparison-bench/notebook.ipynb
uv run python 01-rag/12-comparison-bench/eval.py
```

No LLM calls; no API key needed.

## Key results

See [`eval-snapshot.json`](https://github.com/vinay199129/agentic-ai-engineering/blob/main/01-rag/12-comparison-bench/./eval-snapshot.json) for the rolled-up table.
