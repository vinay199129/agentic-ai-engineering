"""Eval for the ColBERT-style late-interaction leaf.

Builds two indexes over the canonical corpus:

1. **Single-vector** — one document embedding, top-k cosine.
2. **Late-interaction** — one embedding *per token*, MaxSim scoring.

Reports recall@{1,3,5} for each and the index-size ratio.
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections.abc import Callable
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

DIMS = 128
SEED = 0
KS = (1, 3, 5)
MAX_DOC_TOKENS = 96
MAX_QUERY_TOKENS = 24
TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _tokens(text: str, cap: int) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)][:cap]


def _token_matrix(text: str, cap: int) -> np.ndarray:
    toks = _tokens(text, cap)
    if not toks:
        toks = [""]
    return hash_embed(toks, dims=DIMS, seed=SEED)


def _maxsim(q_mat: np.ndarray, d_mat: np.ndarray) -> float:
    """Score one (query, doc) pair via Σ max over token-token similarities."""
    if q_mat.size == 0 or d_mat.size == 0:
        return 0.0
    return float(np.max(q_mat @ d_mat.T, axis=1).sum())


def _recall(retriever: Callable[[str, int], list[str]], qa: list, k: int) -> float:
    hits = sum(1 for q in qa if set(retriever(q.question, k)) & set(q.source_ids))
    return round(hits / len(qa), 4)


def main() -> None:
    docs = load_corpus()
    qa = [q for q in load_golden_qa() if q.source_ids]
    texts = [d.title + ". " + d.abstract for d in docs]
    ids = [d.arxiv_id for d in docs]

    doc_single = hash_embed(texts, dims=DIMS, seed=SEED)
    doc_tokens = [_token_matrix(t, MAX_DOC_TOKENS) for t in texts]

    def retrieve_single(q: str, k: int) -> list[str]:
        qv = hash_embed([q], dims=DIMS, seed=SEED)[0]
        idx, _ = cosine_topk(qv, doc_single, k=k)
        return [ids[int(i)] for i in idx]

    def retrieve_maxsim(q: str, k: int) -> list[str]:
        q_mat = _token_matrix(q, MAX_QUERY_TOKENS)
        scores = np.array([_maxsim(q_mat, d_mat) for d_mat in doc_tokens])
        return [ids[int(i)] for i in np.argsort(-scores)[:k]]

    per_retriever = {
        "single_vector": {f"recall@{k}": _recall(retrieve_single, qa, k) for k in KS},
        "late_interaction_maxsim": {f"recall@{k}": _recall(retrieve_maxsim, qa, k) for k in KS},
    }

    n_doc_vecs_single = len(docs)
    n_doc_vecs_token = int(sum(d.shape[0] for d in doc_tokens))
    index_size_ratio = round(n_doc_vecs_token / max(n_doc_vecs_single, 1), 2)

    snapshot = {
        "technique": "colbert-late-interaction",
        "version": "0.1.0",
        "dataset": "benchmarks/golden-qa/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "n_docs": len(docs),
            "n_questions": len(qa),
            "config": {
                "dims": DIMS,
                "max_doc_tokens": MAX_DOC_TOKENS,
                "max_query_tokens": MAX_QUERY_TOKENS,
            },
            "per_retriever": per_retriever,
            "index_vectors_single": n_doc_vecs_single,
            "index_vectors_late_interaction": n_doc_vecs_token,
            "index_size_ratio_vs_single": index_size_ratio,
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
