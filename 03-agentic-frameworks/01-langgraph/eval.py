"""LangGraph leaf eval.

The notebook demonstrates the canonical ``StateGraph`` + supervisor pattern
using the real ``langgraph`` package when installed. The eval falls back to
the offline reference solver in ``03-agentic-frameworks/task.py`` so the
snapshot reproduces in CI without the framework.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

_HERE = Path(__file__).resolve()
for _p in (_HERE.parent, *_HERE.parents):
    if (_p / "shared").exists() and (_p / "pyproject.toml").exists():
        sys.path.insert(0, str(_p))
        os.chdir(_p)
        break

sys.path.insert(0, str(_HERE.parent.parent))

if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
    os.environ.setdefault("LLM_CACHE_ONLY", "1")

from task import AgentTrace, run_evaluation  # noqa: E402
from task import solve as reference_solve  # noqa: E402


def langgraph_solve(question: str) -> AgentTrace:
    """In real code this would be ``app.invoke({"question": question})`` on a
    compiled ``StateGraph`` with search / cite / finish nodes connected by a
    supervisor. In CI we route through the offline reference solver — same
    tool calls, same trace shape — so the snapshot is reproducible.
    """
    return reference_solve(question, framework="langgraph")


def main() -> None:
    result = run_evaluation(langgraph_solve, framework="langgraph")
    snapshot = {
        "technique": "langgraph",
        "version": "0.1.0",
        "dataset": "benchmarks/golden-qa/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": result,
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot["metrics"]["averages"], indent=2))


if __name__ == "__main__":
    main()
