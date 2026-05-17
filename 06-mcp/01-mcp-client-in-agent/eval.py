"""MCP-client-in-an-agent eval.

Runs the canonical 3-question demo through ``mcp_agent_solve`` and reuses the
same metric shape as ``03-agentic-frameworks/`` so this leaf's snapshot is
directly comparable to the framework tour.
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

from mcp_core import (  # noqa: E402
    Client,
    InProcessTransport,
    build_corpus_server,
    mcp_agent_solve,
)

from shared.loaders import load_golden_qa  # noqa: E402

DEMO_IDS: tuple[str, ...] = ("q01", "q23", "q27")
EXPECTED_TOOLS = {"search_corpus", "fetch_paper", "cite"}


def main() -> None:
    qa = {q.id: q for q in load_golden_qa()}
    server = build_corpus_server()
    client = Client(transport=InProcessTransport(server))
    client.initialize()

    per_q: list[dict[str, Any]] = []
    grounded_hits = 0
    tool_acc_total = 0.0
    n_steps_total = 0
    latency_total = 0.0

    for qid in DEMO_IDS:
        q = qa[qid]
        t0 = time.perf_counter()
        result = mcp_agent_solve(client, q.question)
        latency = (time.perf_counter() - t0) * 1000

        called = {s["name"] for s in result["trace"] if s["role"] == "tool_call"}
        tool_acc = len(called & EXPECTED_TOOLS) / max(len(EXPECTED_TOOLS), 1)
        tool_acc_total += tool_acc

        answer = result["answer"] or ""
        expected_src = list(q.source_ids)
        grounded = (
            any(src in answer for src in expected_src)
            if expected_src
            else "i don't know" in answer.lower()
        )
        grounded_hits += int(grounded)
        n_steps_total += len(result["trace"])
        latency_total += latency

        per_q.append(
            {
                "id": qid,
                "tool_accuracy": round(tool_acc, 4),
                "grounded": grounded,
                "n_steps": len(result["trace"]),
                "latency_ms": round(latency, 3),
                "trace": result["trace"],
            }
        )

    n = len(DEMO_IDS)
    snapshot = {
        "technique": "mcp-client-in-agent",
        "version": "0.1.0",
        "dataset": "benchmarks/golden-qa/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "framework": "mcp-in-process",
            "n_questions": n,
            "averages": {
                "tool_call_accuracy": round(tool_acc_total / n, 4),
                "final_answer_grounded": round(grounded_hits / n, 4),
                "avg_n_steps": round(n_steps_total / n, 3),
                "avg_latency_ms": round(latency_total / n, 3),
            },
            "per_question": per_q,
            "server_audit_calls": len(server.audit_log),
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot["metrics"]["averages"], indent=2))


if __name__ == "__main__":
    main()
