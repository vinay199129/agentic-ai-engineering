!!! info "`03-agentic-frameworks/00-react-from-scratch`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/vinay199129/agentic-ai-engineering/tree/main/03-agentic-frameworks/00-react-from-scratch)

**Headline metrics:** `tool_call_accuracy`=1 · `final_answer_grounded`=0.333

# ReAct from scratch — the algorithm with no framework

**Problem:** Every agent framework wraps the same loop: think → act → observe → repeat. If you can't write that loop in 60 lines of Python you don't really understand what your framework is hiding. This leaf strips ReAct (Yao et al., 2022) to its essence using nothing but the shared LLM shim and the canonical task tools.

**What you'll learn:**
- The ReAct prompt template: `Thought:` / `Action:` / `Observation:` per turn until `Final Answer:`.
- How to parse model output into a tool call without a structured-output API.
- The two failure modes the framework wrappers paper over: parse errors and infinite loops.
- Why a 30-line scratch implementation is the right starting point before reaching for LangGraph.

**When to use it:** As a teaching baseline and a reference implementation. Production should prefer one of the typed frameworks — but you'll debug those better having written this once.

**When NOT to use it:** Production. The scratch loop has no checkpointer, no streaming, no proper structured tool calls, no observability.

## Run it

```powershell
uv run jupyter lab 03-agentic-frameworks/00-react-from-scratch/notebook.ipynb
uv run python 03-agentic-frameworks/00-react-from-scratch/eval.py
```

No framework deps. Uses the shared `03-agentic-frameworks/task.py` tools.

## Key results

See [`eval-snapshot.json`](https://github.com/vinay199129/agentic-ai-engineering/blob/main/03-agentic-frameworks/00-react-from-scratch/./eval-snapshot.json) for the four shared metrics on the 3-question demo set: `tool_call_accuracy`, `final_answer_grounded`, `avg_n_steps`, `avg_latency_ms`.

## References

- Yao et al., [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)
- [LangChain's original ReAct implementation](https://python.langchain.com/v0.1/docs/modules/agents/agent_types/react/) — the source of the prompt format
