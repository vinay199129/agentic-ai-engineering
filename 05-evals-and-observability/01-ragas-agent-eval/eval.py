"""Agent eval: tool-call accuracy + agent goal accuracy + topic adherence.

Operates on the committed `traces.json` fixture so the snapshot is fully
deterministic in CI. The optional LLM judge calls (when an API key is set)
hit the shared cache and add nuance; the deterministic fallback is the
default path for offline runs.
"""

from __future__ import annotations

import json
import os
import re
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

if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
    os.environ.setdefault("LLM_CACHE_ONLY", "1")

from shared.llm import Message, complete  # noqa: E402

MODEL = "openai/gpt-4o-mini"
NS = "05-evals-and-observability/01-ragas-agent-eval"
WORD_RE = re.compile(r"[A-Za-z0-9]+")


def _words(text: str) -> set[str]:
    return {w.lower() for w in WORD_RE.findall(text) if len(w) > 2}


def _judge(system: str, user: str) -> bool | None:
    try:
        reply = (
            complete(
                model=MODEL,
                namespace=NS,
                messages=[
                    Message(role="system", content=system),
                    Message(role="user", content=user),
                ],
            )
            .content.strip()
            .lower()
        )
    except Exception:
        return None
    if reply.startswith("yes"):
        return True
    if reply.startswith("no"):
        return False
    return None


def tool_call_accuracy(trace: list[dict[str, Any]], expected: list[str]) -> float:
    """Did the agent call the expected set of tools (order-insensitive)?"""
    called = [step["name"] for step in trace if step.get("role") == "tool_call"]
    if not expected:
        return 1.0 if not called else 0.0
    hits = sum(1 for tool in expected if tool in called)
    return round(hits / len(expected), 4)


def agent_goal_accuracy(
    user_goal: str, final_answer: str, trace: list[dict[str, Any]] | None = None
) -> float:
    """Does the final answer satisfy the user's goal?"""
    sys_p = (
        "You are a goal-satisfaction judge. Answer 'yes' if the answer satisfies "
        "the user's goal, else 'no'. One token only."
    )
    verdict = _judge(sys_p, f"Goal: {user_goal}\n\nAnswer: {final_answer}\n\nSatisfies?")
    if verdict is not None:
        return 1.0 if verdict else 0.0

    # Heuristic fallback: reject hedges; require either direct goal-word overlap
    # or substantial overlap with the trace's tool outputs (i.e., the answer is
    # grounded in what the agent actually retrieved).
    hedge_markers = (
        "i don't know",
        "could not",
        "somewhere in",
        "please run",
        "next.",
        "weather",
    )
    lower = final_answer.lower()
    if not final_answer.strip() or any(m in lower for m in hedge_markers):
        return 0.0
    if len(final_answer) < 30:
        return 0.0
    answer_words = _words(final_answer)
    goal_words = _words(user_goal)
    goal_overlap = len(goal_words & answer_words) / max(len(goal_words), 1) if goal_words else 0.0
    trace_words: set[str] = set()
    for step in trace or []:
        text = step.get("output_summary") or ""
        text += " " + json.dumps(step.get("arguments", {}))
        trace_words |= _words(text)
    trace_overlap = (
        len(trace_words & answer_words) / max(len(trace_words), 1) if trace_words else 0.0
    )
    return 1.0 if (goal_overlap >= 0.20 or trace_overlap >= 0.20) else 0.0


def topic_adherence(user_goal: str, trace: list[dict[str, Any]]) -> float:
    """Fraction of trace steps whose content stays on the goal's topic."""
    if not trace:
        return 0.0
    goal_words = _words(user_goal)
    if not goal_words:
        return 1.0
    on_topic = 0
    for step in trace:
        text = step.get("output_summary") or step.get("content") or ""
        text += " " + json.dumps(step.get("arguments", {}))
        overlap = len(goal_words & _words(text)) / len(goal_words)
        if overlap >= 0.15:
            on_topic += 1
    return round(on_topic / len(trace), 4)


def main() -> None:
    traces_path = Path(__file__).parent / "traces.json"
    traces = json.loads(traces_path.read_text(encoding="utf-8"))

    per_trace: list[dict[str, Any]] = []
    for t in traces:
        tca = tool_call_accuracy(t["trace"], t["expected_tools"])
        final_answers = [s["content"] for s in t["trace"] if s.get("role") == "final_answer"]
        final = final_answers[-1] if final_answers else ""
        aga = agent_goal_accuracy(t["user_goal"], final, t["trace"])
        ta = topic_adherence(t["user_goal"], t["trace"])
        per_trace.append(
            {
                "id": t["id"],
                "tool_call_accuracy": tca,
                "agent_goal_accuracy": aga,
                "topic_adherence": ta,
            }
        )

    averages = {
        k: round(sum(p[k] for p in per_trace) / max(len(per_trace), 1), 4)
        for k in ("tool_call_accuracy", "agent_goal_accuracy", "topic_adherence")
    }

    snapshot = {
        "technique": "ragas-agent-eval",
        "version": "0.1.0",
        "dataset": "05-evals-and-observability/01-ragas-agent-eval/traces.json",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "n_traces": len(traces),
            "averages": averages,
            "per_trace": per_trace,
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
