!!! info "`05-evals-and-observability/01-ragas-agent-eval`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/vinay199129/agentic-ai-engineering/tree/main/05-evals-and-observability/01-ragas-agent-eval)

**Headline metrics:** `tool_call_accuracy`=0.8

# Agent eval — tool-call accuracy, goal accuracy, topic adherence

**Problem:** RAG metrics evaluate one retrieve-and-generate hop. Agentic systems chain multiple tool calls before answering, and they can fail at *any* step. Three agent-specific metrics catch the most common failures:

- **Tool-call accuracy** — did the agent call the right tool with the right arguments?
- **Agent goal accuracy** — did the final answer satisfy the user's stated goal?
- **Topic adherence** — did the agent stay on-task across the whole trajectory?

**What you'll learn:**
- A small **agent trace** schema (steps + tool calls + final answer) that's portable across LangGraph / Pydantic AI / CrewAI / OpenAI Agents SDK.
- How to score each of the three metrics with cached LLM judges (with deterministic fallbacks).
- A fixture of five synthetic traces covering happy-path, wrong-tool, wrong-args, off-topic, and failed-goal — so the eval shows what *each metric* catches.

**When to use it:** Once your agent does anything beyond a single retrieve-and-generate, add these. The right tool with bad args looks like a retrieval failure on context_precision; only tool-call accuracy will catch it.

**When NOT to use it:** Pure-RAG with no tool use — stick to RAGAS metrics (see `../00-ragas-rag-eval/`). Multi-turn chat without tools — use task-completion metrics instead.

## Run it

```powershell
uv sync --group evals
uv run jupyter lab 05-evals-and-observability/01-ragas-agent-eval/notebook.ipynb
uv run python 05-evals-and-observability/01-ragas-agent-eval/eval.py
```

No live tools or LLMs required — the fixture is committed in `traces.json` so the metrics are fully deterministic in CI.

## Key results

See [`eval-snapshot.json`](https://github.com/vinay199129/agentic-ai-engineering/blob/main/05-evals-and-observability/01-ragas-agent-eval/./eval-snapshot.json) for per-trace breakdown of the three metrics on the synthetic fixture, plus average rates.

## References

- [RAGAS — Agent Metrics](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/agents.html)
- LangChain, [LangSmith for agent evaluation](https://docs.smith.langchain.com/old/evaluation/agents)
- OpenAI, [Evaluating agents — what to measure](https://platform.openai.com/docs/guides/evals)
