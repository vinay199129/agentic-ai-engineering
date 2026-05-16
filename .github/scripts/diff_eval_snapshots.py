"""Compare committed eval-snapshot.json files between two git refs.

Fails (exit 1) when any numeric metric regresses by more than ``--tolerance``
(default 5%) on the head ref compared to the base ref. Direction of "good" is
inferred — recall/faithfulness/precision/accuracy/refusal_rate/pass_rate are
treated as higher-is-better; latency/cost/chunks are treated as lower-is-better.

Only metrics that exist on *both* sides are compared. New metrics on head are
reported but never fail the build. Removed metrics are reported as warnings.

Usage:

    python diff_eval_snapshots.py --base <sha> --head <sha> [--tolerance 0.05]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
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
)
LOWER_IS_BETTER = (
    "latency",
    "cost",
    "tokens",
    "time_ms",
    "duration",
    "errors",
)


def direction(metric_name: str) -> int | None:
    name = metric_name.lower()
    for s in HIGHER_IS_BETTER:
        if s in name:
            return +1
    for s in LOWER_IS_BETTER:
        if s in name:
            return -1
    return None


def flatten(prefix: str, value: Any, out: dict[str, float]) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        out[prefix] = float(value)
    elif isinstance(value, dict):
        for k, v in value.items():
            flatten(f"{prefix}.{k}" if prefix else k, v, out)


def load_snapshot_at(ref: str, path: str) -> dict[str, Any] | None:
    try:
        raw = subprocess.check_output(["git", "show", f"{ref}:{path}"], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def changed_snapshot_paths(base: str, head: str) -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", "--diff-filter=AM", base, head],
            text=True,
        )
    except subprocess.CalledProcessError:
        return []
    return [p.strip() for p in out.splitlines() if p.strip().endswith("eval-snapshot.json")]


def compare(base: dict[str, Any], head: dict[str, Any], tolerance: float) -> list[str]:
    bm = base.get("metrics") or {}
    hm = head.get("metrics") or {}
    flat_base: dict[str, float] = {}
    flat_head: dict[str, float] = {}
    flatten("", bm, flat_base)
    flatten("", hm, flat_head)

    failures: list[str] = []
    for key, head_val in flat_head.items():
        if key not in flat_base:
            continue
        base_val = flat_base[key]
        dir_ = direction(key)
        if dir_ is None or base_val == 0:
            continue
        diff = (head_val - base_val) / abs(base_val)
        regressed = (dir_ > 0 and diff < -tolerance) or (dir_ < 0 and diff > tolerance)
        marker = "FAIL" if regressed else "ok"
        sign = "+" if diff >= 0 else ""
        print(f"  [{marker}] {key}: {base_val:.4f} -> {head_val:.4f} ({sign}{diff:.2%})")
        if regressed:
            failures.append(
                f"{key}: {base_val:.4f} -> {head_val:.4f} ({sign}{diff:.2%}) exceeds +/-{tolerance:.0%}"
            )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--tolerance", type=float, default=0.05)
    args = parser.parse_args()

    paths = changed_snapshot_paths(args.base, args.head)
    if not paths:
        print("No eval-snapshot.json files changed in this PR.")
        return 0

    overall_failures: list[str] = []
    for path in paths:
        base = load_snapshot_at(args.base, path)
        head = load_snapshot_at(args.head, path) or json.loads(
            Path(path).read_text(encoding="utf-8")
        )
        print(f"\n=== {path} ===")
        if base is None:
            print("  (new snapshot — no baseline to compare)")
            continue
        if head is None:
            print("  (snapshot removed)")
            continue
        failures = compare(base, head, args.tolerance)
        for f in failures:
            overall_failures.append(f"{path}: {f}")

    if overall_failures:
        print("\nRegressions:")
        for f in overall_failures:
            print(f"  - {f}")
        print(
            f"\n{len(overall_failures)} metric(s) regressed beyond tolerance. "
            "If intentional, label the PR with `eval-regression-ok` and document the reason."
        )
        return 1
    print("\nAll changed snapshots within tolerance.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
