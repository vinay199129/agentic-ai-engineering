"""Streaming-with-intervention eval.

Drive the graph through ``hitl.stream_events`` (a generator), collect events
until an ``interrupt`` is yielded, then resume and collect the remaining
events. The metrics quantify "did we actually stream, then resume cleanly?".
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve()
for _p in (_HERE.parent, *_HERE.parents):
    if (_p / "shared").exists() and (_p / "pyproject.toml").exists():
        sys.path.insert(0, str(_p))
        os.chdir(_p)
        break

sys.path.insert(0, str(_HERE.parent.parent))

if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
    os.environ.setdefault("LLM_CACHE_ONLY", "1")

from hitl import (  # noqa: E402
    DEMO_IDS,
    Checkpointer,
    Command,
    build_research_graph,
    get_question,
    stream_events,
)


def main() -> None:
    chunks_before_pause_total = 0
    completed_after_resume = 0
    total_chunks = 0
    latency_total = 0.0
    per_q: list[dict[str, Any]] = []

    for qid in DEMO_IDS:
        t0 = time.perf_counter()
        cp = Checkpointer()
        graph = build_research_graph()
        events: list[dict[str, Any]] = []
        chunks_before_pause = 0
        paused_at: str | None = None

        for event in stream_events(
            graph,
            {"question": get_question(qid), "question_id": qid},
            thread_id=qid,
            checkpointer=cp,
        ):
            events.append(event)
            if event["event"] == "interrupt":
                paused_at = event["node"]
                break
            chunks_before_pause += 1

        # Intervene: simulate the user clicking "approve" mid-stream.
        decision = {"approved": True, "reviewer": "stream-user"}
        state = graph.resume(
            thread_id=qid,
            command=Command(resume=decision),
            checkpointer=cp,
        )

        chunks_before_pause_total += chunks_before_pause
        if state.get("published"):
            completed_after_resume += 1
        total_chunks += len(events)

        latency = (time.perf_counter() - t0) * 1000
        latency_total += latency
        per_q.append(
            {
                "id": qid,
                "events_before_pause": len(events) - 1,
                "paused_at": paused_at,
                "completed_after_resume": bool(state.get("published")),
                "final_answer": state.get("final_answer"),
                "latency_ms": round(latency, 3),
            }
        )

    n = len(DEMO_IDS)
    snapshot = {
        "technique": "streaming-with-intervention",
        "version": "0.1.0",
        "dataset": "benchmarks/golden-qa/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "n_questions": n,
            "averages": {
                "chunks_before_pause": round(chunks_before_pause_total / n, 3),
                "stream_completed_after_resume_rate": round(completed_after_resume / n, 4),
                "total_chunks_per_run": round(total_chunks / n, 3),
                "avg_latency_ms": round(latency_total / n, 3),
            },
            "per_question": per_q,
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot["metrics"]["averages"], indent=2))


if __name__ == "__main__":
    main()
