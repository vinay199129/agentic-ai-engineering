"""Microsoft Agent Framework leaf eval.

Real implementation lives in the notebook; CI uses the offline reference
solver so the snapshot is reproducible without the framework's deps.
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


def msaf_solve(question: str) -> AgentTrace:
    """Real version: build a SequentialWorkflow over [researcher, summariser]
    and ``await workflow.run(question)``. The offline reference solver mirrors
    that two-stage shape (search then synthesise) so the metrics are aligned.
    """
    return reference_solve(question, framework="microsoft-agent-framework")


def main() -> None:
    result = run_evaluation(msaf_solve, framework="microsoft-agent-framework")
    snapshot = {
        "technique": "microsoft-agent-framework",
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
