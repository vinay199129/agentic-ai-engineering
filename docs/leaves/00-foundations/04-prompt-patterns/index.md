!!! info "`00-foundations/04-prompt-patterns`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/vinay199129/agentic-ai-engineering/tree/main/00-foundations/04-prompt-patterns)

**Headline metrics:** _no headline metric_

# The five Anthropic workflow patterns

**Problem:** "Agent" is a fuzzy word. Most production "agents" are actually one of five small composition patterns over LLM calls — and naming them makes design decisions concrete.

**What you'll learn:**
- **Prompt chain** — step A's output feeds step B (summarize → critique).
- **Routing** — classify the input, dispatch to a specialized handler.
- **Parallelization** — fan out N attempts concurrently, then judge / aggregate.
- **Orchestrator-workers** — one call decomposes, workers handle each piece in parallel.
- **Evaluator-optimizer** — draft, evaluate, revise until a measurable bar is cleared.

**When to use it:** Any time you're tempted to reach for a framework, first ask which of these five patterns you actually need. Most "agents" are 1–2 of them stacked.

**When NOT to use it:** True open-ended autonomy where you can't enumerate handlers up front — that's where `03-agentic-frameworks/` come in.

## Run it

```powershell
uv sync --group foundations
uv run jupyter lab 00-foundations/04-prompt-patterns/notebook.ipynb
uv run python 00-foundations/04-prompt-patterns/eval.py
```

The eval script writes `eval-snapshot.json` with structural-completeness checks for each pattern (did the chain produce both steps, did the router emit a valid label, did the evaluator return a JSON score, etc.).

## Key results

See [`eval-snapshot.json`](https://github.com/vinay199129/agentic-ai-engineering/blob/main/00-foundations/04-prompt-patterns/./eval-snapshot.json) for the latest numbers.

## References

- Anthropic, [Building effective agents](https://www.anthropic.com/research/building-effective-agents)
- OpenAI, [A practical guide to building agents](https://cdn.openai.com/business-guides/a-practical-guide-to-building-agents.pdf)
