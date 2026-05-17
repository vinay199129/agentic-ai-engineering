"""Edit-state eval.

On each interrupt, the reviewer rewrites the draft with a known-correct
citation (built from the question's expected sources) and approves. The eval
asserts the edit propagates to the downstream ``publish`` node.
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
    get_expected_sources,
    get_question,
)


def _build_corrected_draft(qid: str, current_draft: str) -> str:
    """Construct a citation-rich draft that uses the expected source ids."""
    expected = get_expected_sources(qid)
    if not expected:
        # Unanswerable: the right correction is to refuse.
        return "I cannot answer this question from the provided corpus."
    cites = " ".join(f"[{src}]" for src in expected)
    return f"{cites} Edited by reviewer: {current_draft[:160]}"


def main() -> None:
    edits_applied = 0
    propagated_correctly = 0
    correct_decisions = 0
    latency_total = 0.0
    per_q: list[dict[str, Any]] = []

    for qid in DEMO_IDS:
        t0 = time.perf_counter()
        cp = Checkpointer()
        graph = build_research_graph()
        state = graph.run(
            {"question": get_question(qid), "question_id": qid},
            thread_id=qid,
            checkpointer=cp,
        )
        assert state.get("_interrupt"), "approve node must interrupt"

        original_draft = state["draft"]
        new_draft = _build_corrected_draft(qid, original_draft)
        edit_decision = (
            {"approved": True, "reviewer": "human:editor"}
            if get_expected_sources(qid)
            else {"approved": False, "reviewer": "human:editor"}
        )
        state = graph.resume(
            thread_id=qid,
            command=Command(
                resume=edit_decision,
                update={"draft": new_draft},
            ),
            checkpointer=cp,
        )

        edited = state["draft"] == new_draft
        edits_applied += int(edited)
        # When approved, the published answer should equal the edited draft.
        if state.get("approved"):
            if state.get("final_answer") == new_draft:
                propagated_correctly += 1
        else:
            # When denied, final_answer should be None (nothing published).
            if state.get("final_answer") is None:
                propagated_correctly += 1

        expected = get_expected_sources(qid)
        expected_decision = bool(expected)  # answerable -> approve, else deny
        if bool(state.get("approved")) == expected_decision:
            correct_decisions += 1

        latency = (time.perf_counter() - t0) * 1000
        latency_total += latency
        per_q.append(
            {
                "id": qid,
                "original_draft": original_draft,
                "edited_draft": new_draft,
                "approved": bool(state.get("approved")),
                "published_answer": state.get("final_answer"),
                "edit_applied": edited,
                "latency_ms": round(latency, 3),
            }
        )

    n = len(DEMO_IDS)
    snapshot = {
        "technique": "edit-state",
        "version": "0.1.0",
        "dataset": "benchmarks/golden-qa/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "n_questions": n,
            "averages": {
                "edit_applied_rate": round(edits_applied / n, 4),
                "edit_propagation_accuracy": round(propagated_correctly / n, 4),
                "human_decision_accuracy": round(correct_decisions / n, 4),
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
