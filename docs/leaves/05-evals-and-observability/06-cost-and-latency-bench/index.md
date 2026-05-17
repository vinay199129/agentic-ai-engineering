!!! info "`05-evals-and-observability/06-cost-and-latency-bench`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/vinay199129/agentic-ai-engineering/tree/main/05-evals-and-observability/06-cost-and-latency-bench)

**Headline metrics:** _no headline metric_

# Cost & latency bench — token counts, $/query, ms/query across models

**Problem:** Cost and latency aren't separate concerns from quality — they *are* the deployment constraints. A 0.05-point recall gain at 5× the cost is rarely worth shipping. This leaf measures both side-by-side across a small panel of models.

**What you'll learn:**
- **Token accounting** — input + output tokens per call, using `tiktoken` BPE estimates so the bench works offline.
- **Static price table** — `$/1M input + $/1M output` per model. Updated by editing one dict.
- **Latency proxy** — observed wall-time per call when the cache misses; cache-hit time when LLM_CACHE_ONLY=1 (representative of "in-region cached" prod scenarios).
- A four-model panel: gpt-4o-mini / gpt-4o / claude-3-5-sonnet / groq-llama-3.1-70b — same prompt, side-by-side cost-per-query.

**When to use it:** Before promoting a model from "experimentation" to "default". Whenever the cost of a sub-pipeline (eg the LLM judge) becomes interesting in its own right.

**When NOT to use it:** Tiny corpora where cost is rounding-error noise. Models with usage-based discounts that aren't reflected in the static price table.

## Run it

```powershell
uv sync --group evals
uv run jupyter lab 05-evals-and-observability/06-cost-and-latency-bench/notebook.ipynb
uv run python 05-evals-and-observability/06-cost-and-latency-bench/eval.py
```

Runs offline. Latency measured against the JSONL cache hits when LLM_CACHE_ONLY=1; against the live provider when an API key is set. Token counts use a fixed `tiktoken` encoder (`cl100k_base`) for deterministic offline accounting.

## Key results

See [`eval-snapshot.json`](https://github.com/vinay199129/agentic-ai-engineering/blob/main/05-evals-and-observability/06-cost-and-latency-bench/./eval-snapshot.json) for per-model: average input/output tokens, $/query, ms/query, and the dominated/dominant pareto label (a model is *dominated* if another panel model wins on both axes).

## References

- [tiktoken — OpenAI BPE encoders](https://github.com/openai/tiktoken)
- [LiteLLM pricing dict](https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json) — drop-in replacement for the local price table
- [Latency benchmarking with Artificial Analysis](https://artificialanalysis.ai/)
