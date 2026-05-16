"""Structural completeness checks for the 5 Anthropic workflow patterns.

This isn't a quality eval — it's a contract eval: did each pattern *produce*
the structural outputs it promises? (chain produces both stages, router emits
a valid label, evaluator returns parseable JSON, etc.) Quality of the prose
itself isn't measured here; that would require a strong-model judge and is
deferred to ``05-evals-and-observability/``.

Run from the repo root:

    uv run python 00-foundations/04-prompt-patterns/eval.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

# Make the repo root importable regardless of cwd.
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
NS = "00-foundations/04-prompt-patterns"
ABSTRACT = (
    "We present RA-MoE, a sparse mixture-of-experts architecture in which router "
    "logits are biased toward experts whose recent activation history minimizes "
    "inter-device communication. On a 47B-parameter language model with 32 experts "
    "and top-2 routing, RA-MoE reduces p99 decode latency by 38% relative to "
    "standard learned routing while keeping perplexity within 0.4% of the baseline."
)


def _say(system: str, user: str, *, temperature: float = 0.0, json_mode: bool = False) -> str:
    return complete(
        model=MODEL,
        namespace=NS,
        temperature=temperature,
        response_format={"type": "json_object"} if json_mode else None,
        messages=[Message(role="system", content=system), Message(role="user", content=user)],
    ).content


def eval_prompt_chain() -> bool:
    summary = _say("Summarize the abstract in one tight sentence.", ABSTRACT)
    critique = _say(
        "Critique the following summary in one sentence: does it preserve the key numeric claim?",
        summary,
    )
    return bool(summary.strip()) and bool(critique.strip())


def eval_routing() -> bool:
    label = _say(
        "Classify the request as exactly one of: SUMMARIZE, TRANSLATE, EXPLAIN. "
        "Reply with only the label.",
        "Give me a one-sentence summary of this paper.",
    ).strip()
    return label in {"SUMMARIZE", "TRANSLATE", "EXPLAIN"}


def eval_parallelization() -> bool:
    cands = [
        _say(f"Write a one-sentence summary, attempt #{i + 1}.", ABSTRACT, temperature=0.7)
        for i in range(3)
    ]
    judge_user = (
        "Pick the best one-sentence summary of the abstract. Reply with ONLY the "
        "integer index (0, 1, or 2).\n"
        "Abstract:\n"
        + ABSTRACT
        + "\n\nCandidates:\n"
        + f"0) {cands[0]}\n1) {cands[1]}\n2) {cands[2]}\n"
    )
    pick = _say("You are an impartial judge.", judge_user).strip()
    return pick.isdigit() and 0 <= int(pick) <= 2 and all(c.strip() for c in cands)


def eval_orchestrator_workers() -> bool:
    topics_raw = _say(
        "List 2 short bullet topics worth expanding from this abstract. "
        "One per line, no numbering.",
        ABSTRACT,
    )
    topics = [t.strip() for t in topics_raw.splitlines() if t.strip()]
    if len(topics) < 2:
        return False
    sections = [
        _say(
            f"Expand the topic '{t}' into one tight paragraph grounded in the abstract.",
            ABSTRACT,
        )
        for t in topics
    ]
    return all(len(s) > 40 for s in sections)


def eval_evaluator_optimizer() -> bool:
    draft = _say("Draft a one-sentence summary of the abstract.", ABSTRACT)
    score_raw = _say(
        "Score the following one-sentence summary from 1-5 on faithfulness AND "
        'specificity. Reply with a JSON object {"faithfulness": int, "specificity": int, '
        '"feedback": str}.',
        f"Abstract:\n{ABSTRACT}\n\nSummary:\n{draft}",
        json_mode=True,
    )
    try:
        score = json.loads(score_raw)
    except json.JSONDecodeError:
        return False
    needed = {"faithfulness", "specificity", "feedback"}
    if not needed <= set(score):
        return False
    revised = _say(
        "Revise the summary to address the feedback. Return only the revised one-sentence summary.",
        f"Abstract:\n{ABSTRACT}\n\nDraft:\n{draft}\n\nFeedback: {score['feedback']}",
    )
    return bool(revised.strip()) and revised.strip() != draft.strip()


def main() -> None:
    results = {
        "prompt_chain_pass": eval_prompt_chain(),
        "routing_pass": eval_routing(),
        "parallelization_pass": eval_parallelization(),
        "orchestrator_workers_pass": eval_orchestrator_workers(),
        "evaluator_optimizer_pass": eval_evaluator_optimizer(),
    }
    results["all_patterns_pass_rate"] = sum(1 for v in results.values() if v) / len(results)

    snapshot = {
        "technique": "prompt-patterns",
        "version": "0.1.0",
        "dataset": "synthetic/RA-MoE-abstract",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": results,
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
