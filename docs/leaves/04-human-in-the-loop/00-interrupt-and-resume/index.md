!!! info "`04-human-in-the-loop/00-interrupt-and-resume`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/vinay199129/agentic-ai-engineering/tree/main/04-human-in-the-loop/00-interrupt-and-resume)

**Headline metrics:** _no headline metric_

# Interrupt and resume — the HITL primitive

**Problem:** A production agent must sometimes pause and wait for a human (compliance review, ambiguous tool call, low-confidence answer). The wrong way is to block the worker thread or to keep the LLM context alive in RAM. The right way is to *checkpoint* execution, persist it, and resume later — possibly in a different process, after minutes or days.

**What you'll learn:**
- Why a checkpointer is the heart of LangGraph's HITL design.
- How `interrupt()` raises a structured pause and `Command(resume=...)` injects the human's answer.
- The minimum data you need to persist to truly resume (state, current node, interrupt payload).
- How to write a 200-line in-memory mini-LangGraph that exposes the same surface so you can reason about what the framework hides.

**When to use it:** Any step that must wait for an asynchronous human decision (approval, edit, choice). It's the foundation pattern that the next five leaves specialise.

**When NOT to use it:** Hot loops or sub-second tool calls — the latency of round-tripping through a human dominates. Use confidence thresholds + auto-execute for those.

## Run it

```powershell
uv run jupyter lab 04-human-in-the-loop/00-interrupt-and-resume/notebook.ipynb
uv run python 04-human-in-the-loop/00-interrupt-and-resume/eval.py
```

No framework deps. Uses `04-human-in-the-loop/hitl.py` (the shared mini-runner).

## Key results

See [`eval-snapshot.json`](https://github.com/vinay199129/agentic-ai-engineering/blob/main/04-human-in-the-loop/00-interrupt-and-resume/./eval-snapshot.json) — three demo questions, each
running search → draft → **interrupt** → resume → publish. Tracked metrics:
`interrupt_fire_rate`, `human_decision_accuracy`, `publish_gating_accuracy`,
`avg_latency_ms`.

## References

- LangGraph docs: [Human-in-the-loop](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/)
- LangGraph reference: [`interrupt()`](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.interrupt) and [`Command`](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.Command)
