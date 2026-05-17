!!! info "`03-agentic-frameworks/04-microsoft-agent-framework`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/your-handle/agentic-ai-engineering/tree/main/03-agentic-frameworks/04-microsoft-agent-framework)

**Headline metrics:** `tool_call_accuracy`=1 · `final_answer_grounded`=0.333

# Microsoft Agent Framework — sequential / concurrent / group-chat workflows

**Problem:** Microsoft's [Agent Framework](https://github.com/microsoft/agent-framework) (built on Semantic Kernel's primitives) is one of the few first-party answers to "how do we run multi-agent workflows in production"? It ships three orchestration patterns: **sequential**, **concurrent**, and **group-chat** — and the choice between them is itself a design decision worth understanding.

**What you'll learn:**
- The three orchestration shapes:
  - **Sequential** — agent A → agent B → agent C; passing output along.
  - **Concurrent** — N agents see the same input in parallel; outputs are fanned-in.
  - **Group chat** — agents share a transcript; a manager decides who speaks next.
- When each pattern is appropriate (latency, redundancy, debate quality).
- How the Microsoft framework's `Workflow` abstraction unifies them.

**When to use it:** Enterprise deployments where you've already invested in Semantic Kernel; multi-agent debate / review patterns; concurrency-friendly tasks where N agents' outputs need ranking.

**When NOT to use it:** Small projects — heavier than `pydantic-ai` for a single-agent task. Non-.NET shops sometimes find the docs Python coverage thinner than the C# story (improving fast).

## Run it

```powershell
uv sync --group frameworks
uv add agent-framework  # or semantic-kernel for the agent primitives directly
uv run jupyter lab 03-agentic-frameworks/04-microsoft-agent-framework/notebook.ipynb
uv run python 03-agentic-frameworks/04-microsoft-agent-framework/eval.py
```

CI uses the offline reference solver.

## Key results

See [`eval-snapshot.json`](https://github.com/your-handle/agentic-ai-engineering/blob/main/03-agentic-frameworks/04-microsoft-agent-framework/./eval-snapshot.json) for the four shared metrics on the demo set.

## What this leaf intentionally skips

- Long-running workflows with `Microsoft.Agents.Persistent` — a Phase 8 deployment-pattern topic.
- C# / .NET equivalents — same primitives, different syntax.

## References

- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [Semantic Kernel agents](https://learn.microsoft.com/semantic-kernel/Frameworks/agent/)
- [AutoGen → Agent Framework migration](https://devblogs.microsoft.com/foundry/microsoft-agent-framework-the-open-source-engine-for-agentic-ai-apps/)
