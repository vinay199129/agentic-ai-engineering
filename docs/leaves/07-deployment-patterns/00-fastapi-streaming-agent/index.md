!!! info "`07-deployment-patterns/00-fastapi-streaming-agent`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/vinay199129/agentic-ai-engineering/tree/main/07-deployment-patterns/00-fastapi-streaming-agent)

**Headline metrics:** _no headline metric_

# FastAPI streaming agent — SSE + HITL resume in production

**Problem:** Real users want **token-by-token** output so the app feels alive, plus a way to **intervene** before destructive steps (publish, send email, hit prod). REST-then-poll feels dead; WebSockets are heavy for one-way streams. **Server-Sent Events (SSE)** are the right fit: HTTP-native, proxy-friendly, trivially debuggable, and they coexist with a small POST endpoint for the human's decision.

**What you'll learn:**
- A 60-line FastAPI app exposing two endpoints: `GET /agent/stream` (SSE) and `POST /agent/resume`.
- How to bridge a generator-style agent runner (`hitl.stream_events`) to an SSE response with `sse-starlette`.
- Why interrupt-and-resume is *the* HITL pattern that survives a stateless HTTP front-end: the server holds the checkpoint, the client just POSTs a `decision`.
- Testing the streamer with `TestClient` so the eval has zero external deps.

**When to use it:** Any user-facing agent that takes more than ~3s end-to-end.

**When NOT to use it:** Pure batch / cron jobs.

## Run it

```powershell
uv run uvicorn 07-deployment-patterns.00-fastapi-streaming-agent.app:app --reload
# Then in another shell:
curl -N "http://localhost:8000/agent/stream?question=summarise%20RA-MoE&thread_id=t1"
# When the SSE pauses on an `interrupt` frame, POST a decision:
curl -X POST http://localhost:8000/agent/resume -H "Content-Type: application/json" \
     -d '{"thread_id":"t1","decision":"approve"}'
```

CI/offline:

```powershell
uv run python 07-deployment-patterns/00-fastapi-streaming-agent/eval.py
```

## Key results

The eval drives the app with FastAPI's `TestClient`, asserts:

* SSE stream emits ≥1 `node_started` frame before the `interrupt` pause,
* the agent **does not** publish before the decision arrives,
* `POST /agent/resume` resumes the graph and the final SSE frame is `complete`.

Tracked metrics: `stream_frame_count`, `interrupt_observed`,
`resume_completes`, `avg_latency_ms`.

## References

- [sse-starlette](https://github.com/sysid/sse-starlette)
- [FastAPI background tasks vs streams](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
