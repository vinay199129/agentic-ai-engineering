!!! info "`03-agentic-frameworks/05-openai-agents-sdk`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/vinay199129/agentic-ai-engineering/tree/main/03-agentic-frameworks/05-openai-agents-sdk)

**Headline metrics:** `tool_call_accuracy`=1 · `final_answer_grounded`=0.333

# OpenAI Agents SDK — handoffs, guardrails, sessions

**Problem:** OpenAI's official agent SDK is intentionally minimal: one `Agent` class, one `Runner`, and three primitives that make multi-agent work tractable — **handoffs**, **guardrails**, and **sessions**. The minimalism is the point: it's the API surface you'd hand to a backend engineer who's never built an agent before.

**What you'll learn:**
- `Agent(name=..., instructions=..., tools=..., handoffs=...)` — the one class you'll use.
- `Runner.run(agent, input=...)` — async runner with built-in tracing.
- **Handoffs** — declarative "if this happens, transfer to that agent" routing.
- **Guardrails** — input/output validators that short-circuit unsafe runs.
- **Sessions** — built-in conversation memory.

**When to use it:** Production agents on the OpenAI stack; teams that want a small API surface with first-party support; tracing baked in.

**When NOT to use it:** Multi-provider deployments (the SDK targets OpenAI-compatible APIs); when you need state graphs or code-action agents.

## Run it

```powershell
uv sync --group frameworks
uv add openai-agents
uv run jupyter lab 03-agentic-frameworks/05-openai-agents-sdk/notebook.ipynb
uv run python 03-agentic-frameworks/05-openai-agents-sdk/eval.py
```

CI uses the offline reference solver.

## Key results

See [`eval-snapshot.json`](https://github.com/vinay199129/agentic-ai-engineering/blob/main/03-agentic-frameworks/05-openai-agents-sdk/./eval-snapshot.json) for the four shared metrics on the demo set.

## What this leaf intentionally skips

- The Realtime API hook-ups (voice agents) — out of scope for the hub.
- Vision / multimodal tool use — see `01-rag/10-multimodal-rag/` for that pattern.

## References

- [OpenAI Agents SDK docs](https://openai.github.io/openai-agents-python/)
- [Handoffs deep dive](https://openai.github.io/openai-agents-python/handoffs/)
- [Guardrails pattern](https://openai.github.io/openai-agents-python/guardrails/)
