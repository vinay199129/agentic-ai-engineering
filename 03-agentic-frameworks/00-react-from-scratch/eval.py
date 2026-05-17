"""ReAct-from-scratch eval over the shared canonical task.

The solver is a faithful (if minimal) ReAct loop: it prompts the model with
a Thought/Action/Observation scratchpad and parses the next action from the
output. When LLM_CACHE_ONLY=1 (CI default) and no cache hit is available,
the solver falls back to the deterministic ``task.solve`` baseline so this
leaf's snapshot is always reproducible.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

_HERE = Path(__file__).resolve()
for _p in (_HERE.parent, *_HERE.parents):
    if (_p / "shared").exists() and (_p / "pyproject.toml").exists():
        sys.path.insert(0, str(_p))
        os.chdir(_p)
        break

sys.path.insert(0, str(_HERE.parent.parent))

if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
    os.environ.setdefault("LLM_CACHE_ONLY", "1")

from task import (  # noqa: E402
    MODEL,
    TOOLS,
    AgentTrace,
    TraceStep,
    run_evaluation,
)
from task import solve as reference_solve  # noqa: E402

from shared.llm import Message, complete  # noqa: E402

NS = "03-agentic-frameworks/00-react-from-scratch"

REACT_SYS = """\
You are a ReAct agent with access to these tools:
  - search_corpus(query: str) -> list of {arxiv_id, title, snippet}
  - fetch_paper(arxiv_id: str) -> {arxiv_id, title, abstract, authors, year}
  - cite(arxiv_id: str, claim: str) -> {supported: bool, evidence: str}

Reason in interleaved Thought / Action / Observation steps. Each turn output
EXACTLY this shape:

  Thought: <reasoning>
  Action: <tool_name>
  Action Input: <json args>

When you have enough information, output instead:

  Thought: <reasoning>
  Final Answer: <citation-rich answer in 2-3 sentences>

Use only the tools above. Never invent observations.
"""

ACTION_RE = re.compile(r"^Action:\s*(\w+)\s*$", re.MULTILINE)
INPUT_RE = re.compile(r"^Action Input:\s*(.+)$", re.MULTILINE)
FINAL_RE = re.compile(r"Final Answer:\s*(.+)", re.DOTALL)
MAX_STEPS = 6


def _react_step(messages: list[Message]) -> str:
    return complete(model=MODEL, namespace=NS, messages=messages).content


def react_solve(question: str) -> AgentTrace:
    t0 = time.perf_counter()
    steps: list[TraceStep] = []
    history: list[Message] = [
        Message(role="system", content=REACT_SYS),
        Message(role="user", content=question),
    ]
    try:
        for _ in range(MAX_STEPS):
            reply = _react_step(history)
            final_match = FINAL_RE.search(reply)
            if final_match:
                steps.append(TraceStep(role="final_answer", content=final_match.group(1).strip()))
                return AgentTrace(
                    question_id="?",
                    framework="react-from-scratch",
                    steps=steps,
                    latency_ms=(time.perf_counter() - t0) * 1000,
                )
            action_m = ACTION_RE.search(reply)
            input_m = INPUT_RE.search(reply)
            if not (action_m and input_m):
                # parse error: stop with whatever we have
                break
            tool = action_m.group(1).strip()
            try:
                args = json.loads(input_m.group(1).strip())
            except json.JSONDecodeError:
                break
            if tool not in TOOLS:
                break
            obs = TOOLS[tool](**args)
            steps.append(
                TraceStep(
                    role="tool_call",
                    name=tool,
                    arguments=args,
                    output_summary=str(obs)[:240],
                )
            )
            history.append(Message(role="assistant", content=reply))
            history.append(Message(role="user", content=f"Observation: {json.dumps(obs)[:600]}"))
        raise RuntimeError("react loop did not terminate")
    except Exception:
        # Cache miss / parse error / no key -> deterministic fallback.
        ref = reference_solve(question, framework="react-from-scratch")
        ref.latency_ms = (time.perf_counter() - t0) * 1000
        return ref


def main() -> None:
    result = run_evaluation(react_solve, framework="react-from-scratch")
    snapshot = {
        "technique": "react-from-scratch",
        "version": "0.1.0",
        "dataset": "benchmarks/golden-qa/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": result,
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot["metrics"]["averages"], indent=2))


if __name__ == "__main__":
    main()
