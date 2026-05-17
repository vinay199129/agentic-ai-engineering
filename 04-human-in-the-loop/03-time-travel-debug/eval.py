"""Time-travel-debug eval.

Two flavours of fork to verify the checkpointer behaves like LangGraph's:

* **Branch-on-decision** — fork from the post-``approve``-interrupt checkpoint
  onto a new thread and resume with the OPPOSITE decision; published output
  must differ from the original.
* **Branch-on-state-edit** — fork from the post-``draft`` checkpoint, rewrite
  ``draft`` in place, then re-run the trailing nodes; the new ``published``
  payload must reflect the edit and the original timeline must be unchanged.
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
)

EXPECTED_NODES = {"search", "draft", "approve"}


def _approve(decision: bool, label: str) -> dict[str, Any]:
    return {"approved": decision, "reviewer": f"timeline:{label}"}


def main() -> None:
    coverage_hits = 0
    coverage_total = 0
    decision_forks_diff = 0
    edit_forks_diff = 0
    originals_preserved = 0
    latency_total = 0.0
    per_q: list[dict[str, Any]] = []

    for qid in DEMO_IDS:
        t0 = time.perf_counter()
        cp = Checkpointer()
        graph = build_research_graph()

        # --- original timeline: approve ---------------------------------------
        graph.run(
            {"question": get_question(qid), "question_id": qid},
            thread_id=f"{qid}-orig",
            checkpointer=cp,
        )
        original = graph.resume(
            thread_id=f"{qid}-orig",
            command=Command(resume=_approve(True, "orig")),
            checkpointer=cp,
        )
        history = cp.history(f"{qid}-orig")

        for node in EXPECTED_NODES:
            coverage_total += 1
            if any(c.node == node for c in history):
                coverage_hits += 1

        # --- Fork 1: branch-on-decision ---------------------------------------
        # Find the interrupt checkpoint (latest one with .interrupt set).
        interrupt_cp = next(
            (c for c in reversed(history) if c.interrupt is not None),
            None,
        )
        assert interrupt_cp is not None, "interrupt checkpoint missing"
        cp.fork(
            f"{qid}-orig",
            from_step=interrupt_cp.step,
            new_thread_id=f"{qid}-fork-deny",
        )
        forked_deny = graph.resume(
            thread_id=f"{qid}-fork-deny",
            command=Command(resume=_approve(False, "deny-fork")),
            checkpointer=cp,
        )
        # Original approved + published; fork denied + did not publish.
        if original.get("approved") != forked_deny.get("approved") and original.get(
            "final_answer"
        ) != forked_deny.get("final_answer"):
            decision_forks_diff += 1

        # --- Fork 2: branch-on-state-edit -------------------------------------
        # Fork from the same interrupt step, patch the draft, then resume.
        cp.fork(
            f"{qid}-orig",
            from_step=interrupt_cp.step,
            new_thread_id=f"{qid}-fork-edit",
        )
        new_draft = "[edited] alternate timeline draft."
        forked_edit = graph.resume(
            thread_id=f"{qid}-fork-edit",
            command=Command(
                resume=_approve(True, "edit-fork"),
                update={"draft": new_draft},
            ),
            checkpointer=cp,
        )
        if forked_edit.get("final_answer") != original.get("final_answer"):
            edit_forks_diff += 1

        # --- Assertion: original timeline must be untouched -------------------
        original_now = cp.history(f"{qid}-orig")
        if [c.state.get("draft") for c in original_now] == [c.state.get("draft") for c in history]:
            originals_preserved += 1

        latency = (time.perf_counter() - t0) * 1000
        latency_total += latency
        per_q.append(
            {
                "id": qid,
                "original_draft": original.get("draft"),
                "original_published": original.get("final_answer"),
                "fork_deny_published": forked_deny.get("final_answer"),
                "fork_edit_published": forked_edit.get("final_answer"),
                "history_len": len(history),
                "latency_ms": round(latency, 3),
            }
        )

    n = len(DEMO_IDS)
    snapshot = {
        "technique": "time-travel-debug",
        "version": "0.1.0",
        "dataset": "benchmarks/golden-qa/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "n_questions": n,
            "averages": {
                "checkpoint_history_coverage": round(coverage_hits / max(coverage_total, 1), 4),
                "decision_fork_produced_alternative": round(decision_forks_diff / n, 4),
                "edit_fork_produced_alternative": round(edit_forks_diff / n, 4),
                "original_preserved_after_fork": round(originals_preserved / n, 4),
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
