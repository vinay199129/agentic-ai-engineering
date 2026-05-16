"""Eval for Self-RAG: refusal_rate on unanswerable + supported_correct on answerable."""

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

MODEL = "openai/gpt-4o-mini"
NS = "01-rag/06-self-rag"
SUBSET = ["q01", "q05", "q11", "q27"]


def main() -> None:
    docs = load_corpus()
    qa = {q.id: q for q in load_golden_qa()}
    doc_texts = [d.title + ". " + d.abstract for d in docs]
    doc_ids = [d.arxiv_id for d in docs]
    doc_vecs = hash_embed(doc_texts, dims=256, seed=0)

    def retrieve(q: str, k: int = 3) -> list[tuple[str, str]]:
        qv = hash_embed([q], dims=256, seed=0)[0]
        idx, _ = cosine_topk(qv, doc_vecs, k=k)
        return [(doc_ids[i], doc_texts[i]) for i in idx]

    grader_sys = (
        "You are a strict relevance grader. Given a question and a single passage, "
        "answer with EXACTLY one token: 'yes' if the passage is directly relevant to "
        "answering the question, otherwise 'no'."
    )
    answer_sys = (
        "You are a careful research assistant. Use ONLY the relevant passages provided. "
        "After your answer, on a NEW line output 'SUPPORT: yes' if every claim is "
        "directly supported by the passages, otherwise 'SUPPORT: no'."
    )

    def grade(q: str, passage: str) -> bool:
        out = (
            complete(
                model=MODEL,
                namespace=NS,
                messages=[
                    Message(role="system", content=grader_sys),
                    Message(
                        role="user", content=f"Question: {q}\n\nPassage: {passage}\n\nRelevant?"
                    ),
                ],
            )
            .content.strip()
            .lower()
        )
        return out.startswith("y")

    def answer(q: str, kept: list[tuple[str, str]]) -> tuple[str, bool]:
        ctx = "\n\n".join(f"[{i}] {t}" for i, (_, t) in enumerate(kept)) or "(none)"
        out = complete(
            model=MODEL,
            namespace=NS,
            messages=[
                Message(role="system", content=answer_sys),
                Message(
                    role="user", content=f"Question: {q}\n\nRelevant passages:\n{ctx}\n\nAnswer:"
                ),
            ],
        ).content
        body, _, tail = out.rpartition("SUPPORT:")
        return body.strip(), tail.strip().lower().startswith("y")

    answerable_supported = 0
    answerable_total = 0
    unanswerable_refused = 0
    unanswerable_total = 0
    answerable_doc_hits = 0

    for qid in SUBSET:
        item = qa[qid]
        cands = retrieve(item.question, k=3)
        kept = [(d, t) for d, t in cands if grade(item.question, t)]
        _, supported = answer(item.question, kept)
        if item.source_ids:  # answerable
            answerable_total += 1
            if supported:
                answerable_supported += 1
            if set(d for d, _ in kept) & set(item.source_ids):
                answerable_doc_hits += 1
        else:  # unanswerable
            unanswerable_total += 1
            if not supported:
                unanswerable_refused += 1

    metrics = {
        "n_subset": len(SUBSET),
        "n_answerable": answerable_total,
        "n_unanswerable": unanswerable_total,
        "answerable_support_rate": round(answerable_supported / max(answerable_total, 1), 4),
        "answerable_kept_doc_recall": round(answerable_doc_hits / max(answerable_total, 1), 4),
        "unanswerable_refusal_rate": round(unanswerable_refused / max(unanswerable_total, 1), 4),
    }
    snapshot = {
        "technique": "self-rag",
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
