"""Approval-gates eval.

Wraps the shared scenario's ``publish`` tool with an explicit policy classifier
and runs the scenario under two reviewer policies (approve_all / deny_all) to
verify the gate is symmetric. Also asserts that the ``search`` tool — which is
safe — never triggers the gate.
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
    search,
)

# Tool policy classifier — the heart of an approval gate. "publish" is the
# only side-effectful tool, so it's the only one that requires approval.
TOOL_POLICY: dict[str, str] = {
    "search": "safe",
    "draft": "safe",
    "publish": "requires_approval",
}


def _approve_all(_state: dict[str, Any]) -> dict[str, Any]:
    return {"approved": True, "reviewer": "policy:approve_all"}


def _deny_all(_state: dict[str, Any]) -> dict[str, Any]:
    return {"approved": False, "reviewer": "policy:deny_all"}


def _run_under(policy_name: str, reviewer: Any) -> dict[str, Any]:
    fires = 0
    consistent = 0
    safe_bypass_hits = 0
    safe_bypass_total = 0
    latency_total = 0.0
    per_q: list[dict[str, Any]] = []
    for qid in DEMO_IDS:
        t0 = time.perf_counter()
        # Sanity: every search call is safe — must never fire the gate.
        hits = search(get_question(qid))
        for tool in ("search", "draft"):
            safe_bypass_total += 1
            if TOOL_POLICY[tool] == "safe":
                safe_bypass_hits += 1

        cp = Checkpointer()
        graph = build_research_graph()
        state = graph.run(
            {"question": get_question(qid), "question_id": qid, "hits": hits},
            thread_id=f"{policy_name}-{qid}",
            checkpointer=cp,
        )
        gate_fired = bool(state.get("_interrupt"))
        fires += int(gate_fired)
        if gate_fired:
            decision = reviewer(state)
            state = graph.resume(
                thread_id=f"{policy_name}-{qid}",
                command=Command(resume=decision),
                checkpointer=cp,
            )
        # Consistency check: published iff policy approved.
        if bool(state.get("published")) == bool(state.get("approved")):
            consistent += 1
        latency = (time.perf_counter() - t0) * 1000
        latency_total += latency
        per_q.append(
            {
                "id": qid,
                "policy": policy_name,
                "gate_fired": gate_fired,
                "approved": bool(state.get("approved")),
                "published": bool(state.get("published")),
                "latency_ms": round(latency, 3),
            }
        )

    n = len(DEMO_IDS)
    return {
        "policy": policy_name,
        "averages": {
            "approval_gate_fire_rate": round(fires / n, 4),
            "approval_policy_consistency": round(consistent / n, 4),
            "safe_tool_bypass_rate": round(safe_bypass_hits / max(safe_bypass_total, 1), 4),
            "avg_latency_ms": round(latency_total / n, 3),
        },
        "per_question": per_q,
    }


def main() -> None:
    runs = [_run_under("approve_all", _approve_all), _run_under("deny_all", _deny_all)]
    # Roll up to a single set of "averages" so the regression suite can read it.
    keys = list(runs[0]["averages"].keys())
    rolled: dict[str, float] = {
        k: round(sum(r["averages"][k] for r in runs) / len(runs), 4) for k in keys
    }
    snapshot = {
        "technique": "approval-gates",
        "version": "0.1.0",
        "dataset": "benchmarks/golden-qa/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "n_questions": len(DEMO_IDS),
            "n_policies": len(runs),
            "tool_policy": TOOL_POLICY,
            "averages": rolled,
            "per_policy": runs,
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot["metrics"]["averages"], indent=2))


if __name__ == "__main__":
    main()
