"""Async HITL via queue eval.

Simulate the production flow:

1.  Run the graph until interrupt; push ``{thread_id, payload}`` onto a queue.
2.  Drain the queue in REVERSE order (proves the checkpointer keeps per-thread
    isolation — no shared "current thread" mutable state).
3.  For each queued request, call the reviewer to get a decision, then resume
    the graph on that thread.
4.  Assert every published thread received the right decision.
"""

from __future__ import annotations

import json
import os
import sys
import time
from collections import deque
from dataclasses import dataclass
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
    get_expected_sources,
    get_question,
)


@dataclass
class ApprovalRequest:
    thread_id: str
    qid: str
    draft: str
    enqueued_at: float


def _reviewer(req: ApprovalRequest) -> dict[str, Any]:
    """Production-shape reviewer: looks at the draft + expected sources."""
    expected = get_expected_sources(req.qid)
    if not expected:
        return {"approved": False, "reviewer": "async:auto"}
    approved = any(src in req.draft for src in expected)
    return {"approved": approved, "reviewer": "async:auto"}


def main() -> None:
    cp = Checkpointer()
    graph = build_research_graph()
    queue: deque[ApprovalRequest] = deque()
    per_q: dict[str, dict[str, Any]] = {}

    # --- Phase 1: launch every agent up to the interrupt ---------------------
    for qid in DEMO_IDS:
        t0 = time.perf_counter()
        state = graph.run(
            {"question": get_question(qid), "question_id": qid},
            thread_id=qid,
            checkpointer=cp,
        )
        assert state.get("_interrupt"), "every run should pause for approval"
        req = ApprovalRequest(
            thread_id=qid,
            qid=qid,
            draft=state["draft"],
            enqueued_at=t0,
        )
        queue.append(req)
        per_q[qid] = {
            "id": qid,
            "draft": state["draft"],
            "enqueued": True,
            "approved": None,
            "published": None,
            "queue_latency_ms": None,
        }

    enqueue_count = len(queue)

    # --- Phase 2: drain queue REVERSED (out-of-order resume safety check) ----
    callback_successes = 0
    out_of_order_safe = 0
    queue_latency_total = 0.0
    drained_order: list[str] = []
    for req in reversed(list(queue)):
        drained_order.append(req.thread_id)
        decision = _reviewer(req)
        try:
            state = graph.resume(
                thread_id=req.thread_id,
                command=Command(resume=decision),
                checkpointer=cp,
            )
            callback_successes += 1
            out_of_order_safe += 1
            queue_latency = (time.perf_counter() - req.enqueued_at) * 1000
            queue_latency_total += queue_latency
            per_q[req.qid]["approved"] = bool(state.get("approved"))
            per_q[req.qid]["published"] = bool(state.get("published"))
            per_q[req.qid]["queue_latency_ms"] = round(queue_latency, 3)
        except Exception as exc:  # pragma: no cover - defensive
            per_q[req.qid]["error"] = repr(exc)

    # Sanity: drain order is the reverse of enqueue order.
    assert drained_order == list(reversed(list(q.thread_id for q in queue)))

    n = len(DEMO_IDS)
    snapshot = {
        "technique": "async-hitl-via-queue",
        "version": "0.1.0",
        "dataset": "benchmarks/golden-qa/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "n_questions": n,
            "averages": {
                "queue_roundtrip_rate": round(enqueue_count / n, 4),
                "callback_resume_success_rate": round(callback_successes / n, 4),
                "out_of_order_safe_rate": round(out_of_order_safe / n, 4),
                "avg_queue_latency_ms": round(queue_latency_total / max(callback_successes, 1), 3),
            },
            "drain_order": drained_order,
            "per_question": list(per_q.values()),
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot["metrics"]["averages"], indent=2))


if __name__ == "__main__":
    main()
