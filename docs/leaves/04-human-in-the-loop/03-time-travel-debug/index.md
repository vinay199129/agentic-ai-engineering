!!! info "`04-human-in-the-loop/03-time-travel-debug`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/vinay199129/agentic-ai-engineering/tree/main/04-human-in-the-loop/03-time-travel-debug)

**Headline metrics:** _no headline metric_

# Time-travel debug — rewind to a checkpoint and fork

**Problem:** When an agent goes wrong, the standard reaction is "re-run with the fix" — but that re-runs the *whole* trace, hits all the LLM costs, and loses the comparison point. Time-travel debugging keeps every checkpoint, lets you rewind to any step, and forks an alternate timeline. You see both the original and the fixed run side-by-side and pay only for what changed.

**What you'll learn:**
- How to enumerate the checkpoint history of a thread.
- The `Checkpointer.fork(from_step, new_thread_id)` move: branch the timeline.
- Why "edit the past, re-run the future" is cheaper than "re-run the whole agent".
- The bug-bash pattern: replay a production failure offline, fork at the bad node, patch, compare.

**When to use it:** Post-mortems, eval bisection, agent regression hunts. Indispensable when each LLM step costs real money.

**When NOT to use it:** Production hot path — checkpoint storage adds latency. Use sampling.

## Run it

```powershell
uv run jupyter lab 04-human-in-the-loop/03-time-travel-debug/notebook.ipynb
uv run python 04-human-in-the-loop/03-time-travel-debug/eval.py
```

## Key results

The eval runs each demo question with two forks:

* **Branch-on-decision** — fork from the interrupt and resume with the opposite decision (`fork-deny` vs original's `approve`).
* **Branch-on-state-edit** — fork from the interrupt, patch the draft via `Command(update=...)`, and resume.

Tracked metrics: `checkpoint_history_coverage` (every node appears in
history), `decision_fork_produced_alternative`,
`edit_fork_produced_alternative`, `original_preserved_after_fork`,
`avg_latency_ms`.

## References

- LangGraph: [Time travel](https://langchain-ai.github.io/langgraph/concepts/time-travel/)
- LangGraph: [Replay and fork](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/time-travel/)
