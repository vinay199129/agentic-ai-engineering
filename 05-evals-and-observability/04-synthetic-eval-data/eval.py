"""Synthetic eval-data generation + calibration.

For each document in the canonical corpus, generate one synthetic Q&A pair
either via a cached LLM call or via a deterministic template fallback. Run
the same baseline retriever on both the synthetic and golden Q&A and compare
recall@3 to surface the calibration gap.
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

from shared.embedders import cosine_topk, hash_embed  # noqa: E402
from shared.llm import Message, complete  # noqa: E402
from shared.loaders import load_corpus, load_golden_qa  # noqa: E402

MODEL = "openai/gpt-4o-mini"
NS = "05-evals-and-observability/04-synthetic-eval-data"
DIMS = 256
SEED = 0
K = 3

GEN_SYS = (
    "Read the research abstract and produce ONE high-quality Q&A pair grounded "
    'in the text. Return a JSON object {"question": ..., "answer": ...}. '
    "The question must be directly answerable from the abstract; the answer "
    "must be ≤ 30 words; quote at least one specific number / entity from the abstract."
)

WORD_RE = re.compile(r"[A-Za-z0-9]+")
SENT_RE = re.compile(r"(?<=[.!?])\s+")


def _words(text: str) -> set[str]:
    return {w.lower() for w in WORD_RE.findall(text) if len(w) > 2}


def _template_qa(doc_id: str, abstract: str) -> dict[str, str]:
    """Deterministic fallback: pull the first sentence as a quasi-question seed."""
    sentences = [s.strip() for s in SENT_RE.split(abstract.strip()) if s.strip()]
    if not sentences:
        return {"question": "", "answer": "", "source_id": doc_id}
    headline = sentences[0]
    return {
        "question": f"What does the paper [{doc_id}] state about: {headline[:120]}?",
        "answer": headline[:240],
        "source_id": doc_id,
    }


def generate(doc_id: str, abstract: str) -> dict[str, str]:
    try:
        reply = complete(
            model=MODEL,
            namespace=NS,
            messages=[
                Message(role="system", content=GEN_SYS),
                Message(role="user", content=abstract),
            ],
        ).content
        parsed = json.loads(reply)
        if isinstance(parsed, dict) and "question" in parsed and "answer" in parsed:
            return {
                "question": str(parsed["question"]).strip(),
                "answer": str(parsed["answer"]).strip(),
                "source_id": doc_id,
            }
    except Exception:
        pass
    return _template_qa(doc_id, abstract)


# --- filters ----------------------------------------------------------


def filter_empty(q: dict[str, str]) -> bool:
    return bool(q["question"].strip() and q["answer"].strip())


def filter_answer_in_source(q: dict[str, str], abstract: str) -> bool:
    """Reject answers whose key terms are not in the source abstract."""
    ans_words = _words(q["answer"])
    src_words = _words(abstract)
    if not ans_words:
        return False
    overlap = len(ans_words & src_words) / len(ans_words)
    return overlap >= 0.30


def filter_question_length(q: dict[str, str]) -> bool:
    return 6 <= len(q["question"].split()) <= 40


# --- main -------------------------------------------------------------


def main() -> None:
    docs = load_corpus()
    qa_golden = [q for q in load_golden_qa() if q.source_ids]
    doc_texts = [d.title + ". " + d.abstract for d in docs]
    doc_ids = [d.arxiv_id for d in docs]
    doc_vecs = hash_embed(doc_texts, dims=DIMS, seed=SEED)

    # 1. generate one per doc
    generated = [generate(d.arxiv_id, d.abstract) for d in docs]
    n_generated = len(generated)

    # 2. filter
    drop_empty = 0
    drop_unsupported = 0
    drop_length = 0
    kept: list[dict[str, str]] = []
    for q, d in zip(generated, docs, strict=True):
        if not filter_empty(q):
            drop_empty += 1
            continue
        if not filter_question_length(q):
            drop_length += 1
            continue
        if not filter_answer_in_source(q, d.abstract):
            drop_unsupported += 1
            continue
        kept.append(q)

    # 3. calibration: recall@3 on each set
    def recall_on(qs: list[dict[str, Any]]) -> float:
        if not qs:
            return 0.0
        hits = 0
        for q in qs:
            qv = hash_embed([q["question"]], dims=DIMS, seed=SEED)[0]
            idx, _ = cosine_topk(qv, doc_vecs, k=K)
            retrieved = {doc_ids[i] for i in idx}
            if q["source_id"] in retrieved:
                hits += 1
        return round(hits / len(qs), 4)

    synthetic_recall = recall_on(kept)
    golden_as_dict = [{"question": q.question, "source_id": q.source_ids[0]} for q in qa_golden]
    golden_recall = recall_on(golden_as_dict)
    calibration_gap = round(synthetic_recall - golden_recall, 4)

    # Commit the kept set alongside the snapshot for downstream use.
    set_path = Path(__file__).parent / "generated-qa.jsonl"
    with set_path.open("w", encoding="utf-8") as fh:
        for q in kept:
            fh.write(json.dumps(q) + "\n")

    snapshot = {
        "technique": "synthetic-eval-data",
        "version": "0.1.0",
        "dataset": "benchmarks/corpus/metadata.jsonl",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "n_docs": len(docs),
            "n_generated": n_generated,
            "n_kept": len(kept),
            "drop_empty": drop_empty,
            "drop_length": drop_length,
            "drop_unsupported": drop_unsupported,
            "synthetic_recall@k": synthetic_recall,
            "golden_recall@k": golden_recall,
            "calibration_gap": calibration_gap,
            "k": K,
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
