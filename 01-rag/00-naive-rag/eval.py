"""Eval for naive RAG over the canonical corpus.

Metrics:
    context_recall — fraction of golden source ids present in retrieved top-k.
    refusal_rate_on_unanswerable — fraction of unanswerable Qs the model refused.
    answer_exact_match_direct — fraction of direct Qs whose answer matches reference
        (case-insensitive substring match — the reference is a *signal*, not a strict spec).
    n_queries — denominator (the size of the golden set used).

Run from the repo root:

    uv run python 01-rag/00-naive-rag/eval.py
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
if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
    os.environ.setdefault("LLM_CACHE_ONLY", "1")

from shared.embedders import cosine_topk, hash_embed  # noqa: E402
from shared.llm import Message, complete  # noqa: E402
from shared.loaders import load_corpus, load_golden_qa  # noqa: E402
from shared.prompts import RAG_SYSTEM, rag_user_prompt  # noqa: E402

MODEL = "openai/gpt-4o-mini"
NS = "01-rag/00-naive-rag"
K = 3
EMBED_DIMS = 256
EMBED_SEED = 0


def main() -> None:
    corpus = load_corpus()
    qa = load_golden_qa()

    doc_vecs = hash_embed(
        [d.title + ". " + d.abstract for d in corpus],
        dims=EMBED_DIMS,
        seed=EMBED_SEED,
    )

    def retrieve(question: str) -> list[tuple[str, str]]:
        q_vec = hash_embed([question], dims=EMBED_DIMS, seed=EMBED_SEED)[0]
        idx, _ = cosine_topk(q_vec, doc_vecs, k=K)
        return [(corpus[i].arxiv_id, corpus[i].title + ". " + corpus[i].abstract) for i in idx]

    n = len(qa)
    n_direct = 0
    n_unanswerable = 0
    recall_hits = 0
    refusal_hits = 0
    answer_hits = 0

    for item in qa:
        retrieved = retrieve(item.question)
        retrieved_ids = {doc_id for doc_id, _ in retrieved}

        if item.source_ids:
            present = sum(1 for s in item.source_ids if s in retrieved_ids)
            recall_hits += present / len(item.source_ids)

        reply = complete(
            model=MODEL,
            namespace=NS,
            messages=[
                Message(role="system", content=RAG_SYSTEM),
                Message(role="user", content=rag_user_prompt(item.question, retrieved)),
            ],
        ).content

        if "unanswerable" in item.tags:
            n_unanswerable += 1
            if reply.strip().startswith("I don't know"):
                refusal_hits += 1
        elif "direct" in item.tags:
            n_direct += 1
            if item.answer.strip().lower() in reply.strip().lower():
                answer_hits += 1

    metrics = {
        "context_recall": round(recall_hits / n, 4),
        "refusal_rate_on_unanswerable": (
            round(refusal_hits / n_unanswerable, 4) if n_unanswerable else None
        ),
        "answer_exact_match_direct": (round(answer_hits / n_direct, 4) if n_direct else None),
        "n_queries": n,
        "k": K,
    }
    snapshot = {
        "technique": "naive-rag",
        "version": "0.1.0",
        "dataset": "benchmarks/golden-qa/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": metrics,
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
