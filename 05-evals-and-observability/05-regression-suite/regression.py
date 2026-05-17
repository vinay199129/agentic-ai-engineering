"""Reusable regression-check library.

Loaded by ``eval.py`` and by ``tests/test_no_regression.py``. Mirrors the
direction-aware comparison from ``.github/scripts/diff_eval_snapshots.py`` but
exposes it as a Python API so individual leaves can call it.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HIGHER_IS_BETTER = (
    "recall",
    "precision",
    "faithfulness",
    "relevancy",
    "accuracy",
    "f1",
    "pass_rate",
    "refusal_rate",
    "exact_match",
    "adherence",
    "connectivity",
    "coverage",
)
LOWER_IS_BETTER = (
    "latency",
    "cost",
    "tokens",
    "time_ms",
    "duration",
    "errors",
    "drop_",
)


def direction(metric_name: str) -> int | None:
    """+1 if higher-is-better, -1 if lower-is-better, None if neutral."""
    name = metric_name.lower()
    for s in HIGHER_IS_BETTER:
        if s in name:
            return +1
    for s in LOWER_IS_BETTER:
        if s in name:
            return -1
    return None


def flatten(prefix: str, value: Any, out: dict[str, float]) -> None:
    """Flatten a nested metrics dict to ``dotted.key -> float``. Drops bools."""
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        out[prefix] = float(value)
    elif isinstance(value, dict):
        for k, v in value.items():
            flatten(f"{prefix}.{k}" if prefix else k, v, out)


def walk_snapshots(root: Path) -> Iterator[tuple[Path, dict[str, Any]]]:
    """Yield (path, snapshot) for every committed eval-snapshot.json under ``root``."""
    for path in sorted(root.rglob("eval-snapshot.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        yield path, data


@dataclass
class Regression:
    leaf: str
    metric: str
    base: float
    head: float
    direction: int
    delta_pct: float


def compare_flat(
    base: dict[str, float], head: dict[str, float], tolerance: float
) -> list[Regression]:
    """Return any metric whose change exceeds ``tolerance`` in the bad direction."""
    out: list[Regression] = []
    for key, head_val in head.items():
        if key not in base or base[key] == 0:
            continue
        dir_ = direction(key)
        if dir_ is None:
            continue
        base_val = base[key]
        delta = (head_val - base_val) / abs(base_val)
        bad = (dir_ > 0 and delta < -tolerance) or (dir_ < 0 and delta > tolerance)
        if bad:
            out.append(
                Regression(
                    leaf="",
                    metric=key,
                    base=base_val,
                    head=head_val,
                    direction=dir_,
                    delta_pct=delta,
                )
            )
    return out


__all__ = [
    "HIGHER_IS_BETTER",
    "LOWER_IS_BETTER",
    "Regression",
    "compare_flat",
    "direction",
    "flatten",
    "walk_snapshots",
]
