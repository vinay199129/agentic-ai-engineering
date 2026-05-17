# Streaming with intervention — pause mid-stream, take input, resume

**Problem:** Chat UIs stream tokens for perceived speed. But if you stream into a side-effectful step (e.g. a `publish` button or a destructive tool), the user often wants to *intervene* — abort, tweak the prompt, or supply missing context — *while* the agent is still going. You need a streaming interface that can pause cleanly on demand.

**What you'll learn:**
- Generator-based agent loops: yield `node_complete` / `interrupt` events.
- The handshake: server yields → client receives → user intervenes → client posts back → server resumes.
- Keeping a clean transcript across pause/resume — the trace must reflect both.
- Why SSE + a per-thread checkpointer is the simplest reliable transport.

**When to use it:** Conversational UIs, agentic IDEs, long-running tool chains where the human is watching live.

**When NOT to use it:** Headless batch agents — no human is there to intervene; use approval queues (next leaf) instead.

## Run it

```powershell
uv run jupyter lab 04-human-in-the-loop/04-streaming-with-intervention/notebook.ipynb
uv run python 04-human-in-the-loop/04-streaming-with-intervention/eval.py
```

## Key results

The eval iterates the agent as a stream of events, asserts that at least one
`node_complete` event is delivered **before** the interrupt fires (proving
the stream actually streams), then resumes from the interrupt and consumes
the rest. Tracked metrics: `chunks_before_pause` (avg, lower bound > 1),
`stream_completed_after_resume_rate`, `total_chunks_per_run`,
`avg_latency_ms`.

## References

- LangGraph: [Streaming](https://langchain-ai.github.io/langgraph/concepts/streaming/)
- Server-Sent Events (SSE): the simplest "server pushes events, client posts back" protocol
