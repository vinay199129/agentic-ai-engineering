"""Build dashboard pages from every committed ``eval-snapshot.json``.

Walks the repo for snapshots, classifies each leaf by phase, extracts a small
set of headline metrics that survive the schema differences between leaves,
and writes:

* ``docs/leaderboard.md`` — one big sortable table + per-phase mini-tables.
* ``docs/dashboard.md`` — a "what shipped" overview with hero numbers and
  links into the per-leaf pages.
* ``docs/data/snapshots.json`` — flat JSON of every metric for any future
  client-side dashboard.

Designed to be safe to re-run any time — fully deterministic.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DATA_DIR = DOCS / "data"
SNAPSHOT_NAME = "eval-snapshot.json"

PHASE_TITLES: dict[str, str] = {
    "00-foundations": "Phase 0 — Foundations",
    "01-rag": "Phase 1 — RAG",
    "02-indexing": "Phase 2 — Indexing internals",
    "03-agentic-frameworks": "Phase 3 — Agentic frameworks",
    "04-human-in-the-loop": "Phase 4 — Human-in-the-loop",
    "05-evals-and-observability": "Phase 5 — Evals & observability",
    "06-mcp": "Phase 6 — MCP",
    "07-deployment-patterns": "Phase 7 — Deployment",
}


HEADLINE_KEYS_PRIORITY: tuple[str, ...] = (
    "tool_call_accuracy",
    "tool_call_success_rate",
    "final_answer_grounded",
    "final_answer_correct",
    "faithfulness",
    "context_recall",
    "context_precision",
    "answer_relevancy",
    "answer_exact_match_direct",
    "schema_validity_rate",
    "canonical_method_coverage",
    "initialize_handshake_ok",
    "payload_trim_ratio",
    "regression_detected",
    "n_questions",
    "n_queries",
    "avg_n_steps",
    "avg_latency_ms",
)


def _walk_metrics(node: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(node, dict):
        for k, v in node.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                out.update(_walk_metrics(v, key))
            elif isinstance(v, (int, float, str, bool)) or v is None:
                out[key] = v
    return out


def _short(name: str) -> str:
    return name.split(".")[-1]


def _fmt(v: Any) -> str:
    if isinstance(v, bool):
        return "✅" if v else "❌"
    if isinstance(v, float):
        return f"{v:.3f}".rstrip("0").rstrip(".")
    if v is None:
        return "—"
    return str(v)


def _pick_headlines(metrics_flat: dict[str, Any]) -> list[tuple[str, Any]]:
    seen: set[str] = set()
    chosen: list[tuple[str, Any]] = []
    for priority_key in HEADLINE_KEYS_PRIORITY:
        for full_key, val in metrics_flat.items():
            short = _short(full_key)
            if short == priority_key and short not in seen:
                seen.add(short)
                chosen.append((short, val))
                break
        if len(chosen) >= 4:
            break
    return chosen


def _collect_snapshots() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(ROOT.rglob(SNAPSHOT_NAME)):
        # skip junk
        parts = path.relative_to(ROOT).parts
        if any(
            p.startswith(".") or p in {"site", "site-lite", "build", "node_modules", "__pycache__"}
            for p in parts
        ):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        leaf_dir = path.parent.relative_to(ROOT).as_posix()
        phase_dir = leaf_dir.split("/")[0]
        metrics_flat = _walk_metrics(data.get("metrics", {}))
        rows.append(
            {
                "leaf": leaf_dir,
                "phase": phase_dir,
                "phase_title": PHASE_TITLES.get(phase_dir, phase_dir),
                "technique": data.get("technique", path.parent.name),
                "version": data.get("version", ""),
                "dataset": data.get("dataset", ""),
                "run_id": data.get("run_id", ""),
                "metrics": metrics_flat,
                "headlines": _pick_headlines(metrics_flat),
            }
        )
    return rows


def _render_leaderboard(rows: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    lines.append("# Leaderboard")
    lines.append("")
    lines.append(
        f"Auto-generated from {len(rows)} committed `eval-snapshot.json` files. "
        "Re-built every time the dashboard script runs (see `scripts/build_dashboard.py`)."
    )
    lines.append("")
    lines.append(f"_Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}_")
    lines.append("")

    by_phase: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        by_phase.setdefault(r["phase"], []).append(r)

    for phase in sorted(by_phase):
        phase_rows = by_phase[phase]
        lines.append(f"## {PHASE_TITLES.get(phase, phase)}")
        lines.append("")
        lines.append(f"_{len(phase_rows)} leaves shipped._")
        lines.append("")
        lines.append("| Leaf | Technique | Headline metrics |")
        lines.append("|---|---|---|")
        for r in phase_rows:
            headline_str = (
                " · ".join(f"`{k}`={_fmt(v)}" for k, v in r["headlines"])
                if r["headlines"]
                else "_(no headline metrics found)_"
            )
            leaf_link = f"[`{r['leaf']}`](leaves/{r['leaf']}/index.md)"
            lines.append(f"| {leaf_link} | {r['technique']} | {headline_str} |")
        lines.append("")
    return "\n".join(lines) + "\n"


def _render_dashboard(rows: list[dict[str, Any]]) -> str:
    by_phase: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        by_phase.setdefault(r["phase"], []).append(r)

    lines: list[str] = []
    lines.append("# Dashboard")
    lines.append("")
    lines.append("**What shipped, at a glance.** Numbers come from the live snapshots.")
    lines.append("")
    lines.append("!!! tip \"Try it in your browser\"")
    lines.append(
        "    A bundled **JupyterLite** site at <a href=\"lite/index.html\"><code>/lite/</code></a> "
        "lets you execute 39 from-scratch leaves in this tab — no install, no API keys."
    )
    lines.append("")

    # hero stats
    n_total = len(rows)
    n_phases = len(by_phase)
    lines.append("## At a glance")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---:|")
    lines.append(f"| Phases shipped | **{n_phases}** |")
    lines.append(f"| Leaves with committed snapshots | **{n_total}** |")
    lines.append("| From-scratch implementation LOC | **~4 200** |")
    lines.append(
        "| Notebooks runnable in browser (Pyodide) | **39** (see "
        "[`browser-execution.md`](browser-execution.md)) |"
    )
    lines.append("")

    lines.append("## Per-phase coverage")
    lines.append("")
    lines.append("| Phase | Leaves | Latest snapshot |")
    lines.append("|---|---:|---|")
    for phase in sorted(by_phase):
        phase_rows = by_phase[phase]
        latest = max((r["run_id"] for r in phase_rows if r["run_id"]), default="—")
        lines.append(f"| {PHASE_TITLES.get(phase, phase)} | {len(phase_rows)} | `{latest}` |")
    lines.append("")

    lines.append("## Where to go next")
    lines.append("")
    lines.append("- **[Leaderboard](leaderboard.md)** — every leaf with its headline metrics.")
    lines.append(
        "- **[Built from scratch](from-scratch.md)** — what we re-implemented and why."
    )
    lines.append(
        "- **[Real-world case studies](case-studies.md)** — every leaf mapped to a production scenario."
    )
    lines.append(
        "- **[Run in browser](browser-execution.md)** — execute the from-scratch leaves with zero install."
    )
    lines.append(
        "- **[Deep-dives](deep-dives/index.md)** — long-form write-ups of the five highest-signal techniques."
    )
    lines.append("")

    return "\n".join(lines) + "\n"


def main() -> None:
    rows = _collect_snapshots()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "snapshots.json").write_text(
        json.dumps(rows, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (DOCS / "leaderboard.md").write_text(_render_leaderboard(rows), encoding="utf-8")
    (DOCS / "dashboard.md").write_text(_render_dashboard(rows), encoding="utf-8")
    print(f"Wrote dashboard + leaderboard from {len(rows)} snapshots.")


if __name__ == "__main__":
    main()
