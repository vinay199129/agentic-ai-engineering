# Async HITL via queue — long-running agents + out-of-band approval

**Problem:** Real production agents run for minutes to hours (research, batch document processing, scheduled jobs). Holding an HTTP request open while waiting for a human to click "approve" is fragile, blocks workers, and can't survive a redeploy. The correct pattern is to **persist the interrupt onto a queue**, return immediately, and let a separate webhook resume the run when the human responds — possibly hours later, in a different process.

**What you'll learn:**
- Modeling an approval as `(thread_id, payload)` rows on a queue.
- The webhook contract: receive `{thread_id, decision}`, resume the graph, return.
- Why this pattern is just `interrupt + checkpointer + queue + callback`.
- How to express the same scenario as a Slack/email round-trip without changing the agent code.

**When to use it:** Long-running agentic workflows, agents that span human shifts, batch jobs that need spot human guidance.

**When NOT to use it:** Sub-second interactive flows — the queue + webhook overhead dominates.

## Run it

```powershell
uv run jupyter lab 04-human-in-the-loop/05-async-hitl-via-queue/notebook.ipynb
uv run python 04-human-in-the-loop/05-async-hitl-via-queue/eval.py
```

## Key results

The eval simulates a queue (an in-memory deque), enqueues every interrupt, has
a separate worker drain the queue and call back into the graph. Tracked
metrics: `queue_roundtrip_rate` (every interrupt should hit the queue exactly
once), `callback_resume_success_rate`, `out_of_order_safe_rate` (resumes in
reversed-enqueue order to prove the checkpointer scopes per `thread_id`),
`avg_queue_latency_ms`.

## References

- Slack Block Kit interactive messages — the most common production transport
- LangGraph: [Custom auth & async resume](https://langchain-ai.github.io/langgraph/concepts/persistence/#async-resume)
