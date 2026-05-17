# CrewAI — roles, tasks, hierarchical crews

**Problem:** When the problem decomposes naturally into roles (researcher, summariser, fact-checker), modelling each agent's *job* explicitly is more legible than a generic ReAct loop. CrewAI bakes that role-based decomposition into the framework.

**What you'll learn:**
- The `role / goal / backstory` triple — how CrewAI encodes an agent's persona.
- `Task(description=..., agent=...)` — work items, not free-floating prompts.
- `Crew(agents=..., tasks=..., process=Process.sequential)` — sequential vs hierarchical orchestration.
- The crews idea: small specialists beat one generalist when the steps are clearly bounded.

**When to use it:** Multi-step pipelines with cleanly separable roles. Demos and stakeholder presentations — the role/goal/backstory format reads like a business document.

**When NOT to use it:** Tight tool-use loops where the bare ReAct or LangGraph topology is a better fit. Latency-sensitive agents (CrewAI tends to do more LLM calls).

## Run it

```powershell
uv sync --group frameworks
uv add crewai
uv run jupyter lab 03-agentic-frameworks/03-crewai/notebook.ipynb
uv run python 03-agentic-frameworks/03-crewai/eval.py
```

CI uses the offline reference solver.

## Key results

See [`eval-snapshot.json`](./eval-snapshot.json) for the four shared metrics on the demo set.

## What this leaf intentionally skips

- Hierarchical (`Process.hierarchical`) crews with a manager LLM — see `07-framework-comparison/` for when to choose hierarchical over sequential.
- Custom memory backends — CrewAI's memory module is a separate topic.

## References

- [CrewAI docs](https://docs.crewai.com/)
- [Role-based agent design (CrewAI blog)](https://blog.crewai.com/)
