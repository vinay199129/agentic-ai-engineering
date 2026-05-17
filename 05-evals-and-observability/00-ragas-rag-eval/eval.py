"""RAGAS-style RAG eval: faithfulness, context_precision, context_recall, answer_relevancy.

All four metrics use ``shared.llm.complete()`` so judge prompts hit the shared
cache. When no key is configured and the cache misses, each metric falls back
to a deterministic n-gram heuristic so the snapshot is always reproducible.
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections.abc import Iterable
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
NS = "05-evals-and-observability/00-ragas-rag-eval"
K = 3
DIMS = 256
SEED = 0
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
WORD_RE = re.compile(r"[A-Za-z0-9]+")


def _words(text: str) -> set[str]:
    return {w.lower() for w in WORD_RE.findall(text) if len(w) > 2}


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in SENT_SPLIT.split(text.strip()) if s.strip()]


def _ask_yesno(system: str, user: str) -> bool | None:
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


# --- four metrics --------------------------------------------------------


def context_precision(question: str, contexts: Iterable[str]) -> float:
    """Of the retrieved contexts, how many are *useful* for the question?"""
    sys_p = (
        "You are a strict relevance judge. Answer with EXACTLY one token: "
        "'yes' if the passage is useful for answering the question, else 'no'."
    )
    contexts = list(contexts)
    if not contexts:
        return 0.0
    hits = 0
    q_words = _words(question)
    for ctx in contexts:
        verdict = _ask_yesno(sys_p, f"Question: {question}\n\nPassage: {ctx}\n\nUseful?")
        if verdict is None:
            # Heuristic fallback: word overlap > 10%.
            overlap = len(q_words & _words(ctx)) / max(len(q_words), 1)
            verdict = overlap > 0.10
        if verdict:
            hits += 1
    return round(hits / len(contexts), 4)


def context_recall(question: str, reference_answer: str, contexts: Iterable[str]) -> float:
    """Of the claims in the reference, how many are recoverable from the contexts?"""
    sentences = _sentences(reference_answer)
    if not sentences:
        return 0.0
    joined = " \n ".join(contexts)
    joined_words = _words(joined)
    sys_p = (
        "You are a strict grounding judge. Answer 'yes' if the claim is entailed "
        "by the passages, else 'no'. One token only."
    )
    hits = 0
    for sent in sentences:
        verdict = _ask_yesno(sys_p, f"Claim: {sent}\n\nPassages:\n{joined}\n\nEntailed?")
        if verdict is None:
            sent_words = _words(sent)
            verdict = len(sent_words & joined_words) / max(len(sent_words), 1) > 0.4
        if verdict:
            hits += 1
    return round(hits / len(sentences), 4)


def faithfulness(answer: str, contexts: Iterable[str]) -> float:
    """Are the claims in the answer supported by the contexts (anti-hallucination)?"""
    sentences = _sentences(answer)
    if not sentences:
        return 0.0
    joined = " \n ".join(contexts)
    joined_words = _words(joined)
    sys_p = (
        "You are a faithfulness judge. Answer 'yes' if the claim is supported by "
        "the passages, else 'no'. One token only."
    )
    hits = 0
    for sent in sentences:
        verdict = _ask_yesno(sys_p, f"Claim: {sent}\n\nPassages:\n{joined}\n\nSupported?")
        if verdict is None:
            sent_words = _words(sent)
            verdict = len(sent_words & joined_words) / max(len(sent_words), 1) > 0.4
        if verdict:
            hits += 1
    return round(hits / len(sentences), 4)


def answer_relevancy(question: str, answer: str) -> float:
    """How directly does the answer address the question? Embedding-cosine proxy."""
    if not answer.strip():
        return 0.0
    qv = hash_embed([question], dims=DIMS, seed=SEED)[0]
    av = hash_embed([answer], dims=DIMS, seed=SEED)[0]
    score = float((qv @ av) / ((float((qv @ qv) ** 0.5) * float((av @ av) ** 0.5)) + 1e-9))
    return round(max(0.0, min(1.0, score)), 4)


# --- run -----------------------------------------------------------------


def main() -> None:
    docs = load_corpus()
    qa = [q for q in load_golden_qa() if q.source_ids]
    doc_texts = [d.title + ". " + d.abstract for d in docs]
    doc_ids = [d.arxiv_id for d in docs]
    doc_vecs = hash_embed(doc_texts, dims=DIMS, seed=SEED)

    def retrieve(question: str) -> list[tuple[str, str]]:
        qv = hash_embed([question], dims=DIMS, seed=SEED)[0]
        idx, _ = cosine_topk(qv, doc_vecs, k=K)
        return [(doc_ids[i], doc_texts[i]) for i in idx]

    def generate(question: str, retrieved: list[tuple[str, str]]) -> str:
        try:
            return complete(
                model=MODEL,
                namespace=NS,
                messages=[
                    Message(role="system", content=RAG_SYSTEM),
                    Message(role="user", content=rag_user_prompt(question, retrieved)),
                ],
            ).content
        except Exception:
            return retrieved[0][1] if retrieved else ""

    per_q: list[dict[str, float | str]] = []
    sums = {
        "context_precision": 0.0,
        "context_recall": 0.0,
        "faithfulness": 0.0,
        "answer_relevancy": 0.0,
    }
    for item in qa:
        retrieved = retrieve(item.question)
        ctxs = [t for _, t in retrieved]
        answer = generate(item.question, retrieved)
        cp = context_precision(item.question, ctxs)
        cr = context_recall(item.question, item.answer, ctxs)
        ff = faithfulness(answer, ctxs)
        ar = answer_relevancy(item.question, answer)
        per_q.append(
            {
                "id": item.id,
                "context_precision": cp,
                "context_recall": cr,
                "faithfulness": ff,
                "answer_relevancy": ar,
            }
        )
        sums["context_precision"] += cp
        sums["context_recall"] += cr
        sums["faithfulness"] += ff
        sums["answer_relevancy"] += ar

    n = max(len(qa), 1)
    averages = {k: round(v / n, 4) for k, v in sums.items()}

    snapshot = {
        "technique": "ragas-rag-eval",
        "version": "0.1.0",
        "dataset": "benchmarks/golden-qa/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "n_questions": len(qa),
            "k": K,
            "averages": averages,
            "per_question_first_5": per_q[:5],
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
