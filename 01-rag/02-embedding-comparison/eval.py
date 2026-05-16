"""Eval for the embedding-comparison leaf.

Runs the same three deterministic-hashing configurations as the notebook
(tiny-128 / balanced-256 / large-512) across the answerable golden Q&A subset
and records recall@{1, 3, 5} per configuration.

Run from the repo root:

    uv run python 01-rag/02-embedding-comparison/eval.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve()
for _p in (_HERE.parent, *_HERE.parents):
    if (_p / "shared").exists() and (_p / "pyproject.toml").exists():
        sys.path.insert(0, str(_p))
        os.chdir(_p)
        break

from shared.embedders import cosine_topk, hash_embed  # noqa: E402
from shared.loaders import load_corpus, load_golden_qa  # noqa: E402

CONFIGS: dict[str, dict[str, object]] = {
    "tiny-128": {"dims": 128, "ngram": (1, 1), "seed": 11},
    "balanced-256": {"dims": 256, "ngram": (1, 2), "seed": 22},
    "large-512": {"dims": 512, "ngram": (1, 2), "seed": 33},
}
KS = (1, 3, 5)


def recall_at_k(
    doc_vecs: np.ndarray,
    q_vecs: np.ndarray,
    doc_ids: list[str],
    qa: list,
    k: int,
) -> float:
    hits = 0
    for i, item in enumerate(qa):
        idx, _ = cosine_topk(q_vecs[i], doc_vecs, k=k)
        retrieved = {doc_ids[j] for j in idx}
        if set(item.source_ids) & retrieved:
            hits += 1
    return round(hits / len(qa), 4)


def main() -> None:
    docs = load_corpus()
    qa = [q for q in load_golden_qa() if q.source_ids]
    doc_texts = [d.title + ". " + d.abstract for d in docs]
    doc_ids = [d.arxiv_id for d in docs]
    q_texts = [q.question for q in qa]

    metrics: dict[str, object] = {"n_docs": len(docs), "n_questions": len(qa)}
    per_config: dict[str, dict[str, float]] = {}
    for name, kwargs in CONFIGS.items():
        doc_vecs = hash_embed(doc_texts, **kwargs)  # type: ignore[arg-type]
        q_vecs = hash_embed(q_texts, **kwargs)  # type: ignore[arg-type]
        per_config[name] = {
            f"recall@{k}": recall_at_k(doc_vecs, q_vecs, doc_ids, qa, k) for k in KS
        }
    metrics["per_config"] = per_config

    snapshot = {
        "technique": "embedding-comparison",
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
