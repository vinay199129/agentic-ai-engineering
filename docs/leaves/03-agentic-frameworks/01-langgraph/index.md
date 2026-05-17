!!! info "`03-agentic-frameworks/01-langgraph`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/vinay199129/agentic-ai-engineering/tree/main/03-agentic-frameworks/01-langgraph)

**Headline metrics:** `tool_call_accuracy`=1 · `final_answer_grounded`=0.333

# LangGraph — stateful graphs

**Problem:** Once an agent has more than one tool, branching, and memory, the bare ReAct loop becomes a mess. LangGraph's answer: model the agent as a **graph** — typed nodes, typed state, conditional edges, a checkpointer.

**What you'll learn:**
- `StateGraph` — declarative agent topology with shared state.
- The **supervisor pattern**: a routing node decides which worker (search vs cite vs finish) runs next.
- Conditional edges (`add_conditional_edges`) — what makes LangGraph *not* just a chain.
- Checkpointers — pause/resume agents at any node (the foundation for HITL in Phase 6).

**When to use it:** Any agent with non-trivial branching or where you need to pause/resume mid-run. The HITL phase (`04-human-in-the-loop/`) builds directly on this leaf.

**When NOT to use it:** Linear pipelines or single-tool agents — overkill. Use Pydantic AI or a flat ReAct loop.

## Run it

```powershell
uv sync --group frameworks
# the framework code:
uv add langgraph langchain-core
uv run jupyter lab 03-agentic-frameworks/01-langgraph/notebook.ipynb
uv run python 03-agentic-frameworks/01-langgraph/eval.py
```

The eval falls back to the shared offline solver when `langgraph` isn't installed or `LLM_CACHE_ONLY=1`, so it runs in CI without the framework.

## Key results

See [`eval-snapshot.json`](https://github.com/vinay199129/agentic-ai-engineering/blob/main/03-agentic-frameworks/01-langgraph/./eval-snapshot.json) for the four shared metrics (`tool_call_accuracy`, `final_answer_grounded`, `avg_n_steps`, `avg_latency_ms`) on the 3-question demo set.

## What this leaf intentionally skips

- Subgraphs and parallel branches — covered conceptually in `07-framework-comparison/`.
- Streaming token-by-token — see `00-foundations/03-streaming-patterns/`.
- The HITL `interrupt()` flow — that's Phase 6 / `04-human-in-the-loop/`.

## References

- [LangGraph docs](https://langchain-ai.github.io/langgraph/)
- [Supervisor multi-agent pattern](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor/)
- [Checkpointers (the persistence layer)](https://langchain-ai.github.io/langgraph/concepts/persistence/)
