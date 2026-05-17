"""LLM-as-judge eval: rubric, pairwise, position-swap.

Reads ``pairs.json`` (committed fixture) and runs three judge patterns over it.
Cached LLM calls when available; deterministic fallbacks otherwise so the
snapshot reproduces in CI.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

_HERE = Path(__file__).resolve()
for _p in (_HERE.parent, *_HERE.parents):
    if (_p / "shared").exists() and (_p / "pyproject.toml").exists():
        sys.path.insert(0, str(_p))
        os.chdir(_p)
        break

if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
    os.environ.setdefault("LLM_CACHE_ONLY", "1")

from shared.llm import Message, complete  # noqa: E402

MODEL = "openai/gpt-4o-mini"
NS = "05-evals-and-observability/03-llm-as-judge"
WORD_RE = re.compile(r"[A-Za-z0-9]+")


def _ask(system: str, user: str) -> str | None:
    try:
        return complete(
            model=MODEL,
            namespace=NS,
            messages=[Message(role="system", content=system), Message(role="user", content=user)],
        ).content.strip()
    except Exception:
        return None


def _words(text: str) -> set[str]:
    return {w.lower() for w in WORD_RE.findall(text) if len(w) > 2}


# --- rubric judge --------------------------------------------------------

RUBRIC_SYS = (
    "You are a strict grader. Score the answer on a 0-4 integer scale: "
    "0=irrelevant, 1=mostly wrong, 2=partially right, 3=mostly right, "
    "4=perfectly faithful and specific. Respond with ONLY the integer."
)


def rubric_score(question: str, answer: str) -> int:
    reply = _ask(RUBRIC_SYS, f"Question: {question}\n\nAnswer: {answer}\n\nScore (0-4):")
    if reply is not None and reply[:1].isdigit():
        try:
            return max(0, min(4, int(reply[:1])))
        except ValueError:
            pass
    # Heuristic: longer + entity-overlap = higher.
    if not answer.strip() or "i don't know" in answer.lower():
        return 1
    overlap = len(_words(question) & _words(answer)) / max(len(_words(question)), 1)
    if overlap >= 0.4 and len(answer) >= 80:
        return 4
    if overlap >= 0.25 and len(answer) >= 40:
        return 3
    if overlap >= 0.15:
        return 2
    return 1


# --- pairwise judge ------------------------------------------------------

PAIRWISE_SYS = (
    "You are an evaluator picking the better answer. Reply with EXACTLY one token: "
    "'A' if answer A is better, 'B' if answer B is better, 'tie' if they are equivalent."
)


def pairwise(question: str, a: str, b: str) -> Literal["A", "B", "tie"]:
    reply = _ask(
        PAIRWISE_SYS, f"Question: {question}\n\n[A] {a}\n\n[B] {b}\n\nBetter (A / B / tie)?"
    )
    if reply:
        head = reply.strip().split()[0].strip(".,").upper()
        if head in {"A", "B"}:
            return head  # type: ignore[return-value]
        if head.lower() == "tie":
            return "tie"
    # Heuristic fallback: prefer the answer with more question-word overlap.
    # If overlaps are equal, prefer the longer answer; tie on full match.
    qw = _words(question)
    over_a = len(qw & _words(a)) / max(len(qw), 1)
    over_b = len(qw & _words(b)) / max(len(qw), 1)
    if abs(over_a - over_b) < 1e-6:
        if abs(len(a) - len(b)) < 5:
            return "tie"
        return "A" if len(a) > len(b) else "B"
    return "A" if over_a > over_b else "B"


# --- position-swap mitigated -------------------------------------------


def pairwise_swapped(question: str, a: str, b: str) -> Literal["A", "B", "tie"]:
    """Vote = A if both orderings prefer A, B if both prefer B, else tie."""
    forward = pairwise(question, a, b)
    backward = pairwise(question, b, a)
    # When the order is flipped, "A" in the backward call means b is preferred.
    backward_remapped: Literal["A", "B", "tie"] = (
        "B" if backward == "A" else "A" if backward == "B" else "tie"
    )
    if forward == backward_remapped:
        return forward
    return "tie"


def main() -> None:
    pairs = json.loads((Path(__file__).parent / "pairs.json").read_text(encoding="utf-8"))

    rubric_hist = {"a": [0] * 5, "b": [0] * 5}
    raw_wins = {"A": 0, "B": 0, "tie": 0}
    swap_wins = {"A": 0, "B": 0, "tie": 0}
    per_pair: list[dict[str, Any]] = []

    for p in pairs:
        ra = rubric_score(p["question"], p["answer_a"])
        rb = rubric_score(p["question"], p["answer_b"])
        rubric_hist["a"][ra] += 1
        rubric_hist["b"][rb] += 1
        raw = pairwise(p["question"], p["answer_a"], p["answer_b"])
        sw = pairwise_swapped(p["question"], p["answer_a"], p["answer_b"])
        raw_wins[raw] += 1
        swap_wins[sw] += 1
        per_pair.append({"id": p["id"], "rubric_a": ra, "rubric_b": rb, "raw": raw, "swap": sw})

    n = max(len(pairs), 1)
    a_raw_rate = raw_wins["A"] / n
    a_swap_rate = swap_wins["A"] / n
    position_bias_delta = round(a_raw_rate - a_swap_rate, 4)

    snapshot = {
        "technique": "llm-as-judge",
        "version": "0.1.0",
        "dataset": "05-evals-and-observability/03-llm-as-judge/pairs.json",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "n_pairs": len(pairs),
            "rubric_hist": rubric_hist,
            "raw_wins": raw_wins,
            "swap_wins": swap_wins,
            "position_bias_delta_a": position_bias_delta,
            "per_pair": per_pair,
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
