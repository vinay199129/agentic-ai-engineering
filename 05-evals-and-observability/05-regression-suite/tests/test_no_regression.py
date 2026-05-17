"""Pytest regression tests for committed eval-snapshots.

These tests intentionally do NOT fail when ``baseline.json`` is absent (a leaf
without an opt-in baseline shouldn't break CI). They DO fail when the baseline
exists and a metric drifts past tolerance — that's the explicit per-leaf
guard pattern this folder exists to demonstrate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_LEAF = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_LEAF))

from regression import compare_flat, flatten, walk_snapshots  # noqa: E402

_HERE = Path(__file__).resolve()
for _p in _HERE.parents:
    if (_p / "shared").exists() and (_p / "pyproject.toml").exists():
        REPO_ROOT = _p
        break
else:  # pragma: no cover - safety
    REPO_ROOT = Path.cwd()

BASELINE = _LEAF / "baseline.json"
TOLERANCE = 0.05


def _by_tech() -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for path, snap in walk_snapshots(REPO_ROOT):
        if path == _LEAF / "eval-snapshot.json":
            continue
        flat: dict[str, float] = {}
        flatten("", snap.get("metrics") or {}, flat)
        tech = snap.get("technique") or path.parent.name
        out[tech] = flat
    return out


def test_every_snapshot_has_required_keys() -> None:
    required = {"technique", "version", "dataset", "run_id", "metrics"}
    for path, snap in walk_snapshots(REPO_ROOT):
        if path == _LEAF / "eval-snapshot.json":
            continue
        missing = required - set(snap.keys())
        assert not missing, f"{path}: missing keys {missing}"


def test_every_snapshot_metrics_is_dict() -> None:
    for path, snap in walk_snapshots(REPO_ROOT):
        assert isinstance(snap.get("metrics"), dict), f"{path}: metrics is not a dict"


@pytest.mark.skipif(not BASELINE.exists(), reason="No baseline.json — opt-in regression check.")
def test_no_regression_vs_baseline() -> None:
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    current = _by_tech()
    all_regressions = []
    for tech, flat in current.items():
        base_for_tech = baseline.get(tech, {})
        for r in compare_flat(base_for_tech, flat, tolerance=TOLERANCE):
            all_regressions.append((tech, r))
    assert not all_regressions, "\n".join(
        f"{t}: {r.metric} {r.base:.4f} -> {r.head:.4f} ({r.delta_pct:+.2%})"
        for t, r in all_regressions
    )
