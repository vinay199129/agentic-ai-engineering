"""FastAPI streaming agent + HITL resume.

Two endpoints:

* ``GET /agent/stream?question=...&thread_id=...`` — Server-Sent Events;
  emits one frame per node start/finish, then an ``interrupt`` frame
  when the agent hits the human-approval gate. The stream stays open;
  it does NOT terminate at the interrupt.
* ``POST /agent/resume`` — body ``{thread_id, decision}``. Resumes the
  paused graph; the open SSE stream receives the post-interrupt frames
  (publish or skip) and finally a ``complete`` frame.

Pure-Python fallback: this module imports the in-repo ``hitl`` runner so
no LangGraph install is required for the demo. Swap the import for the
real LangGraph graph in production — the SSE shape is identical.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from collections import defaultdict
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

# Repo bootstrap: make `hitl` importable.
_HERE = Path(__file__).resolve()
for _p in (_HERE.parent, *_HERE.parents):
    if (_p / "shared").exists() and (_p / "pyproject.toml").exists():
        sys.path.insert(0, str(_p))
        sys.path.insert(0, str(_p / "04-human-in-the-loop"))
        break

os.environ.setdefault("LLM_CACHE_ONLY", "1")

from fastapi import FastAPI, HTTPException  # noqa: E402
from hitl import Checkpointer, Command, build_research_graph, stream_events  # noqa: E402
from pydantic import BaseModel  # noqa: E402

app = FastAPI(title="agentic-streaming-demo", version="0.1.0")


class _ThreadState:
    """Per-thread coordination: a queue of frames + a future for the decision."""

    def __init__(self) -> None:
        self.queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.decision: asyncio.Future[str] | None = None
        self.done: bool = False


THREADS: dict[str, _ThreadState] = defaultdict(_ThreadState)


class ResumeBody(BaseModel):
    thread_id: str
    decision: str  # "approve" | "deny"


async def _run_agent(thread_id: str, question: str) -> None:
    """Drive the graph and push every event onto the thread's queue.

    ``stream_events`` walks the graph one node at a time and stops at the
    interrupt. We then wait for the human decision, call ``graph.resume``,
    and emit synthetic ``node_complete``/``complete`` events for the
    post-interrupt nodes so the SSE client sees a single continuous stream.
    """
    state = THREADS[thread_id]
    loop = asyncio.get_running_loop()
    graph = build_research_graph()
    checkpointer = Checkpointer()

    def _stream_pre_interrupt() -> bool:
        """Drive the graph up to interrupt or completion. Returns True if interrupted."""
        interrupted = False
        for ev in stream_events(
            graph,
            {"question": question},
            thread_id=thread_id,
            checkpointer=checkpointer,
        ):
            asyncio.run_coroutine_threadsafe(state.queue.put(ev), loop)
            if ev.get("event") == "interrupt":
                interrupted = True
        return interrupted

    try:
        was_interrupted = await asyncio.to_thread(_stream_pre_interrupt)
        if was_interrupted:
            decision = await _await_decision(thread_id)
            approved = decision.lower() == "approve"
            cmd = Command(resume={"approved": approved, "reviewer": "user"})
            final_state = await asyncio.to_thread(
                graph.resume,
                thread_id=thread_id,
                command=cmd,
                checkpointer=checkpointer,
            )
            await state.queue.put(
                {
                    "event": "node_complete",
                    "node": "publish",
                    "delta_keys": ["published", "final_answer"],
                    "published": bool(final_state.get("published")),
                }
            )
    finally:
        await state.queue.put({"event": "complete"})
        state.done = True


async def _await_decision(thread_id: str) -> str:
    state = THREADS[thread_id]
    if state.decision is None:
        state.decision = asyncio.get_running_loop().create_future()
    return await state.decision


@app.get("/agent/stream")
async def agent_stream(question: str, thread_id: str) -> Any:
    """SSE endpoint. Yields ``data: {json}\\n\\n`` frames as the graph progresses."""
    from sse_starlette.sse import EventSourceResponse

    state = THREADS[thread_id]
    # Pre-create the decision future so /agent/resume never races against
    # the worker task.
    if state.decision is None:
        state.decision = asyncio.get_running_loop().create_future()
    task = asyncio.create_task(_run_agent(thread_id, question))

    async def _events() -> AsyncGenerator[dict[str, Any], None]:
        try:
            while True:
                ev = await state.queue.get()
                yield {"event": ev.get("event", "message"), "data": json.dumps(ev)}
                if ev.get("event") == "complete":
                    return
        finally:
            if not task.done():
                task.cancel()

    return EventSourceResponse(_events())


@app.post("/agent/resume")
async def agent_resume(body: ResumeBody) -> dict[str, str]:
    state = THREADS.get(body.thread_id)
    if state is None or state.decision is None:
        raise HTTPException(status_code=409, detail="no_pending_interrupt")
    if state.decision.done():
        raise HTTPException(status_code=409, detail="decision_already_provided")
    state.decision.set_result(body.decision)
    return {"status": "resumed"}


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
