"""Cost & latency bench across a small model panel.

Runs the same RAG-style prompt through each model in ``PANEL``. When the JSONL
cache has a hit, we measure the cache-hit time as a proxy for "warm" latency;
when it doesn't, we either hit the live API (if a key is configured) or fall
back to a deterministic synthetic latency draw so the snapshot is reproducible.

Token counts use a fixed tiktoken encoder (cl100k_base) so they don't depend
on a network call or on which provider answered.
"""

from __future__ import annotations

import json
import os
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

if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
    os.environ.setdefault("LLM_CACHE_ONLY", "1")

from shared.llm import Message, complete  # noqa: E402
from shared.loaders import load_corpus, load_golden_qa  # noqa: E402
from shared.prompts import RAG_SYSTEM, rag_user_prompt  # noqa: E402

NS = "05-evals-and-observability/06-cost-and-latency-bench"

# (provider/model, in $/1M, out $/1M, synthetic_ms when no cache + no key)
PANEL: list[tuple[str, float, float, float]] = [
    ("openai/gpt-4o-mini", 0.15, 0.60, 320.0),
    ("openai/gpt-4o", 2.50, 10.00, 540.0),
    ("anthropic/claude-3-5-sonnet-20241022", 3.00, 15.00, 620.0),
    ("groq/llama-3.1-70b-versatile", 0.59, 0.79, 180.0),
]

DEMO_IDS = ["q01", "q05", "q11", "q15", "q23"]


def _count_tokens(text: str) -> int:
    try:
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        # ~4 chars/token rule of thumb.
        return max(1, len(text) // 4)


def _synthetic_response(question: str) -> str:
    # Deterministic offline output so output tokens are stable.
    return f"Based on the provided context, the answer is grounded in the source. (re: {question[:60]})"


def main() -> None:
    docs = load_corpus()
    qa = {q.id: q for q in load_golden_qa()}
    doc_texts = [d.title + ". " + d.abstract for d in docs]
    doc_ids = [d.arxiv_id for d in docs]

    contexts: list[list[tuple[str, str]]] = []
    for qid in DEMO_IDS:
        item = qa[qid]
        contexts.append([(doc_ids[i], doc_texts[i]) for i in range(min(3, len(docs)))])
        _ = item  # context selection is intentionally trivial here

    per_model: dict[str, dict[str, float | str]] = {}
    for model, p_in, p_out, synth_ms in PANEL:
        tot_in = tot_out = 0
        tot_ms = 0.0
        for qid, ctx in zip(DEMO_IDS, contexts, strict=True):
            user = rag_user_prompt(qa[qid].question, ctx)
            tot_in += _count_tokens(RAG_SYSTEM) + _count_tokens(user)
            t0 = time.perf_counter()
            try:
                reply = complete(
                    model=model,
                    namespace=NS,
                    messages=[
                        Message(role="system", content=RAG_SYSTEM),
                        Message(role="user", content=user),
                    ],
                ).content
                obs_ms = (time.perf_counter() - t0) * 1000
            except Exception:
                reply = _synthetic_response(qa[qid].question)
                obs_ms = synth_ms
            tot_out += _count_tokens(reply)
            tot_ms += obs_ms

        n = len(DEMO_IDS)
        avg_in = tot_in / n
        avg_out = tot_out / n
        avg_ms = round(tot_ms / n, 3)
        cost = round((avg_in * p_in + avg_out * p_out) / 1_000_000, 6)
        per_model[model] = {
            "avg_input_tokens": round(avg_in, 2),
            "avg_output_tokens": round(avg_out, 2),
            "avg_latency_ms": avg_ms,
            "cost_per_query_usd": cost,
        }

    # Pareto frontier — a model is dominated if another wins on both cost & latency.
    def dominated(model: str) -> bool:
        a = per_model[model]
        for other, b in per_model.items():
            if other == model:
                continue
            if (
                float(b["cost_per_query_usd"]) <= float(a["cost_per_query_usd"])
                and float(b["avg_latency_ms"]) <= float(a["avg_latency_ms"])
                and (
                    float(b["cost_per_query_usd"]) < float(a["cost_per_query_usd"])
                    or float(b["avg_latency_ms"]) < float(a["avg_latency_ms"])
                )
            ):
                return True
        return False

    for m in per_model:
        per_model[m]["pareto"] = "dominated" if dominated(m) else "non-dominated"

    snapshot = {
        "technique": "cost-and-latency-bench",
        "version": "0.1.0",
        "dataset": "benchmarks/golden-qa/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "n_queries": len(DEMO_IDS),
            "demo_question_ids": DEMO_IDS,
            "per_model": per_model,
            "price_table_source": "static (see eval.py PANEL)",
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
