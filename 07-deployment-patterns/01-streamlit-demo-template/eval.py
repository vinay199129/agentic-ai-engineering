"""Structural + solver eval for the Streamlit template.

Imports the module (no Streamlit context required), checks the public
surface, runs the default offline solver against several canonical
questions, and verifies the trace shape.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

_HERE = Path(__file__).resolve()
for _p in (_HERE.parent, *_HERE.parents):
    if (_p / "shared").exists() and (_p / "pyproject.toml").exists():
        sys.path.insert(0, str(_p))
        os.chdir(_p)
        break

sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent.parent.parent / "06-mcp"))

os.environ.setdefault("LLM_CACHE_ONLY", "1")


def main() -> None:
    import app  # type: ignore

    required = ("run", "solve_demo", "render_message")
    surface_complete = all(callable(getattr(app, name, None)) for name in required)

    questions = [
        "What does RA-MoE do?",
        "Summarise the contributions of paper synth-001.",
        "How does the safety paper recommend running evals?",
    ]
    successes = 0
    trace_lens: list[int] = []
    t0 = time.perf_counter()
    for q in questions:
        result = app.solve_demo(q)
        trace = result.get("trace", [])
        trace_lens.append(len(trace))
        if isinstance(result, dict) and result.get("answer") and trace:
            successes += 1
    latency = (time.perf_counter() - t0) * 1000

    snapshot = {
        "technique": "streamlit-demo-template",
        "version": "0.1.0",
        "dataset": "shared/qa-3",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "averages": {
                "module_import_ok": 1.0,
                "public_surface_complete": float(surface_complete),
                "demo_solve_success_rate": round(successes / len(questions), 4),
                "avg_trace_steps": round(sum(trace_lens) / len(trace_lens), 2),
                "avg_latency_ms": round(latency / len(questions), 3),
            },
            "trace_lens": trace_lens,
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot["metrics"]["averages"], indent=2))


if __name__ == "__main__":
    main()
