!!! info "`03-agentic-frameworks/02-pydantic-ai`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/your-handle/agentic-ai-engineering/tree/main/03-agentic-frameworks/02-pydantic-ai)

**Headline metrics:** `tool_call_accuracy`=1 · `final_answer_grounded`=0.333

# Pydantic AI — type-safe agents with typed deps and structured output

**Problem:** Most agent frameworks return free-form text. When you wire an agent into a real codebase, you want **types**: typed dependencies passed in, typed output coming back, so the rest of your code can compose on it without parsing strings.

**What you'll learn:**
- `Agent[DepsT, OutputT]` — a single class parameterised by *what the tools see* and *what the agent returns*.
- Tool registration via `@agent.tool` — type hints become the JSON schema, no boilerplate.
- Structured output — when you set `output_type=PaperSummary`, the agent returns a Pydantic model, not a string.
- The mental model: **Pydantic AI is the strict-mode version of the OpenAI Python client**.

**When to use it:** Anywhere you'd hate to parse free-form text — APIs, code generation, data pipelines. Excellent for "the agent is a single shaped function call".

**When NOT to use it:** Highly branched multi-agent workflows — LangGraph / CrewAI are better fits.

## Run it

```powershell
uv sync --group frameworks
uv add pydantic-ai
uv run jupyter lab 03-agentic-frameworks/02-pydantic-ai/notebook.ipynb
uv run python 03-agentic-frameworks/02-pydantic-ai/eval.py
```

CI uses the offline reference solver.

## Key results

See [`eval-snapshot.json`](https://github.com/your-handle/agentic-ai-engineering/blob/main/03-agentic-frameworks/02-pydantic-ai/./eval-snapshot.json) for the four shared metrics on the 3-question demo set.

## What this leaf intentionally skips

- Streaming via `agent.run_stream(...)` — same code, plus an async-iterator.
- Pydantic AI's multi-agent handoff (the SDK is intentionally minimal here).

## References

- [Pydantic AI docs](https://ai.pydantic.dev/)
- [Why Pydantic AI exists (blog post)](https://pydantic.dev/articles/pydantic-ai)
- See also: `00-foundations/01-structured-outputs/` for the structured-output pattern in pure Python.
