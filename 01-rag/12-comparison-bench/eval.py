"""Eval for comparison-bench: aggregates all sibling eval-snapshot.json into a table."""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve()
for _p in (_HERE.parent, *_HERE.parents):
    if (_p / "shared").exists() and (_p / "pyproject.toml").exists():
        sys.path.insert(0, str(_p))
        os.chdir(_p)
        break

from shared.paths import repo_root  # noqa: E402

ROOT = repo_root() / "01-rag"

HEADLINES: dict[str, tuple[str, str]] = {
    "naive-rag": ("metrics.context_recall", "context_recall"),
    "chunking-strategies": (
        "metrics.per_strategy.fixed.avg_chunks_per_doc",
        "avg chunks/doc (fixed)",
    ),
    "embedding-comparison": ("metrics.per_config.large-512.recall@3", "recall@3 (large-512)"),
    "hybrid-search": ("metrics.per_retriever.hybrid_rrf.recall@3", "recall@3 (hybrid RRF)"),
    "reranking": ("metrics.recall@1.llm", "recall@1 (LLM reranker)"),
    "query-transformation": ("metrics.per_strategy.hyde.recall@3", "recall@3 (HyDE)"),
    "self-rag": ("metrics.unanswerable_refusal_rate", "refusal_rate (unanswerable)"),
    "corrective-rag": ("metrics.verdict_accuracy", "verdict_accuracy"),
    "agentic-rag": ("metrics.route_accuracy", "route_accuracy"),
    "long-context-rag": ("metrics.recall@3.contextual", "recall@3 (contextual)"),
    "graph-rag": ("metrics.n_communities", "n_communities"),
    "multimodal-rag": ("metrics.recall@3.joint", "recall@3 (joint)"),
}


def walk(d: Any, path: str) -> Any:
    cur = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def main() -> None:
    rows: list[dict[str, Any]] = []
    for sub in sorted(ROOT.iterdir()):
        snap = sub / "eval-snapshot.json"
        if not snap.is_file() or sub.name == "12-comparison-bench":
            continue
        data = json.loads(snap.read_text())
        tech = data.get("technique", sub.name)
        spec = HEADLINES.get(tech)
        if spec is None:
            rows.append({"leaf": sub.name, "technique": tech, "metric": None, "value": None})
            continue
        path, label = spec
        rows.append(
            {"leaf": sub.name, "technique": tech, "metric": label, "value": walk(data, path)}
        )

    md_lines = ["| leaf | technique | headline metric | value |", "| --- | --- | --- | --- |"]
    for r in rows:
        md_lines.append(
            f"| `{r['leaf']}` | {r['technique']} | {r['metric'] or '—'} | {r['value']} |"
        )
    table = "\n".join(md_lines)
    print(table)

    snapshot = {
        "technique": "comparison-bench",
        "version": "0.1.0",
        "dataset": "01-rag/*/eval-snapshot.json",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "n_techniques_indexed": len(rows),
            "n_with_value": sum(1 for r in rows if r["value"] is not None),
            "rows": rows,
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    leaderboard = Path(__file__).parent / "leaderboard.md"
    leaderboard.write_text(table + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
