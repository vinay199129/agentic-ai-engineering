"""Framework-comparison eval: aggregate sibling snapshots into a matrix.

Reads every sibling leaf's ``eval-snapshot.json`` and joins it with the
hand-curated feature matrix below to produce ``leaderboard.md`` + a
machine-readable snapshot.
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

from shared.paths import repo_root  # noqa: E402

ROOT = repo_root() / "03-agentic-frameworks"


# --- Hand-curated feature matrix -----------------------------------------
# Columns are abilities you'd ask for in a buying conversation.
# Marks: + = first-class, ~ = partial / convention, - = absent.
FEATURE_MATRIX: dict[str, dict[str, str]] = {
    "react-from-scratch": {
        "typed_io": "-",
        "graph_state": "-",
        "conditional_routing": "-",
        "streaming": "-",
        "checkpointer": "-",
        "code_action": "-",
        "handoffs": "-",
        "vendor": "self",
    },
    "langgraph": {
        "typed_io": "~",
        "graph_state": "+",
        "conditional_routing": "+",
        "streaming": "+",
        "checkpointer": "+",
        "code_action": "-",
        "handoffs": "~",
        "vendor": "LangChain",
    },
    "pydantic-ai": {
        "typed_io": "+",
        "graph_state": "-",
        "conditional_routing": "~",
        "streaming": "+",
        "checkpointer": "-",
        "code_action": "-",
        "handoffs": "-",
        "vendor": "Pydantic",
    },
    "crewai": {
        "typed_io": "~",
        "graph_state": "-",
        "conditional_routing": "~",
        "streaming": "~",
        "checkpointer": "-",
        "code_action": "-",
        "handoffs": "~",
        "vendor": "CrewAI",
    },
    "microsoft-agent-framework": {
        "typed_io": "~",
        "graph_state": "+",
        "conditional_routing": "+",
        "streaming": "+",
        "checkpointer": "+",
        "code_action": "-",
        "handoffs": "+",
        "vendor": "Microsoft",
    },
    "openai-agents-sdk": {
        "typed_io": "~",
        "graph_state": "-",
        "conditional_routing": "+",
        "streaming": "+",
        "checkpointer": "~",
        "code_action": "-",
        "handoffs": "+",
        "vendor": "OpenAI",
    },
    "smolagents": {
        "typed_io": "~",
        "graph_state": "-",
        "conditional_routing": "~",
        "streaming": "+",
        "checkpointer": "-",
        "code_action": "+",
        "handoffs": "-",
        "vendor": "HuggingFace",
    },
}

PICK_WHEN = {
    "react-from-scratch": "you're teaching, debugging, or building a one-off.",
    "langgraph": "you need branchy multi-agent topologies + checkpoint-based HITL.",
    "pydantic-ai": "you want type-safe, structured-output agents in a typed Python codebase.",
    "crewai": "the task decomposes into named roles you can describe to a stakeholder.",
    "microsoft-agent-framework": "you're inside the Microsoft / Semantic Kernel ecosystem and want production-grade multi-agent workflows.",
    "openai-agents-sdk": "you're on the OpenAI stack and want the smallest possible production API.",
    "smolagents": "your reasoning benefits from code as the action (math, compositional steps, data wrangling).",
}


def _load_sibling_snapshots() -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for sub in sorted(ROOT.iterdir()):
        if not sub.is_dir() or sub.name == "07-framework-comparison":
            continue
        snap_path = sub / "eval-snapshot.json"
        if not snap_path.exists():
            continue
        snap = json.loads(snap_path.read_text(encoding="utf-8"))
        tech = snap.get("technique", sub.name)
        averages = (snap.get("metrics") or {}).get("averages") or {}
        out[tech] = {k: float(v) for k, v in averages.items() if isinstance(v, (int, float))}
    return out


def _render_leaderboard(
    metrics: dict[str, dict[str, float]], features: dict[str, dict[str, str]]
) -> str:
    metric_cols = ["tool_call_accuracy", "final_answer_grounded", "avg_n_steps", "avg_latency_ms"]
    feature_cols = [
        "typed_io",
        "graph_state",
        "conditional_routing",
        "streaming",
        "checkpointer",
        "code_action",
        "handoffs",
    ]

    lines: list[str] = []
    lines.append("# Agentic-frameworks leaderboard\n")
    lines.append("## Metrics (same canonical task)\n")
    header = "| framework | " + " | ".join(metric_cols) + " |"
    sep = "| --- | " + " | ".join(["---"] * len(metric_cols)) + " |"
    lines.append(header)
    lines.append(sep)
    for tech in features:
        row = metrics.get(tech, {})
        cells = []
        for col in metric_cols:
            v = row.get(col)
            cells.append(f"{v:.4f}" if isinstance(v, float) else "—")
        lines.append(f"| `{tech}` | " + " | ".join(cells) + " |")

    lines.append("\n## Capability matrix\n")
    header = "| framework | " + " | ".join(feature_cols) + " | vendor |"
    sep = "| --- | " + " | ".join(["---"] * (len(feature_cols) + 1)) + " |"
    lines.append(header)
    lines.append(sep)
    for tech, feats in features.items():
        cells = [feats.get(col, "?") for col in feature_cols] + [feats.get("vendor", "?")]
        lines.append(f"| `{tech}` | " + " | ".join(cells) + " |")

    lines.append("\n*+ = first-class; ~ = partial / convention; - = absent*\n")

    lines.append("## Pick this framework when…\n")
    for tech, when in PICK_WHEN.items():
        lines.append(f"* **`{tech}`** — {when}")

    return "\n".join(lines) + "\n"


def main() -> None:
    metrics = _load_sibling_snapshots()
    leaderboard = _render_leaderboard(metrics, FEATURE_MATRIX)
    out_md = Path(__file__).parent / "leaderboard.md"
    out_md.write_text(leaderboard, encoding="utf-8")

    snapshot = {
        "technique": "framework-comparison",
        "version": "0.1.0",
        "dataset": "03-agentic-frameworks/*/eval-snapshot.json",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "n_frameworks_indexed": len(FEATURE_MATRIX),
            "n_with_metrics": len(metrics),
            "feature_matrix": FEATURE_MATRIX,
            "metrics_by_framework": metrics,
        },
    }
    out_json = Path(__file__).parent / "eval-snapshot.json"
    out_json.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(leaderboard)


if __name__ == "__main__":
    main()
