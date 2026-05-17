"""Regression suite eval: aggregate every committed eval-snapshot.json.

Produces a meta-snapshot describing the entire eval inventory: how many
snapshots exist, how many flat metrics they expose, and how many would
regress vs the committed ``baseline.json`` at the default 5% tolerance.

Run from the repo root:

    uv run python 05-evals-and-observability/05-regression-suite/eval.py
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

sys.path.insert(0, str(_HERE.parent))

from regression import compare_flat, direction, flatten, walk_snapshots  # noqa: E402

from shared.paths import repo_root  # noqa: E402

ROOT = repo_root()
SELF = _HERE.parent / "eval-snapshot.json"
BASELINE = _HERE.parent / "baseline.json"
TOLERANCE = 0.05


def main() -> None:
    by_technique: dict[str, dict[str, float]] = {}
    n_snapshots = 0
    n_metrics_total = 0
    n_higher = n_lower = n_neutral = 0

    for path, snap in walk_snapshots(ROOT):
        # Skip ourselves so we don't compare a meta-snapshot against itself.
        if path.resolve() == SELF.resolve():
            continue
        n_snapshots += 1
        flat: dict[str, float] = {}
        flatten("", snap.get("metrics") or {}, flat)
        n_metrics_total += len(flat)
        for k in flat:
            d = direction(k)
            if d is None:
                n_neutral += 1
            elif d > 0:
                n_higher += 1
            else:
                n_lower += 1
        tech = snap.get("technique") or path.parent.name
        by_technique[tech] = flat

    # --- compare against baseline (if present) -----------------------
    regressions: list[dict[str, str | float]] = []
    if BASELINE.exists():
        baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
        for tech, flat in by_technique.items():
            base_for_tech = baseline.get(tech, {})
            for r in compare_flat(base_for_tech, flat, tolerance=TOLERANCE):
                regressions.append(
                    {
                        "technique": tech,
                        "metric": r.metric,
                        "base": r.base,
                        "head": r.head,
                        "delta_pct": round(r.delta_pct, 4),
                    }
                )

    snapshot = {
        "technique": "regression-suite",
        "version": "0.1.0",
        "dataset": "all-eval-snapshots",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "n_snapshots": n_snapshots,
            "n_metrics_total": n_metrics_total,
            "n_higher_is_better": n_higher,
            "n_lower_is_better": n_lower,
            "n_neutral_metrics": n_neutral,
            "tolerance": TOLERANCE,
            "baseline_present": BASELINE.exists(),
            "n_regressions_vs_baseline": len(regressions),
            "regressions_vs_baseline": regressions,
        },
    }
    SELF.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
