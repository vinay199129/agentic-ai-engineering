"""Eval for BM25 internals + hybrid retrieval.

Reports recall@{1,3,5} across:
    - TF-IDF baseline (BM25 with k1 ~ infinity, b = 0)
    - BM25 with (k1=1.5, b=0.75)
    - Dense (shared hash embedder)
    - RRF fusion of dense + BM25
    - Weighted linear fusion swept over alpha in [0, 1]

The single ``alpha_star`` recorded is the alpha that maximised recall@3.
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

from rank_bm25 import BM25Okapi  # noqa: E402

from shared.embedders import cosine_topk, hash_embed  # noqa: E402
from shared.loaders import load_corpus, load_golden_qa  # noqa: E402

DIMS = 256
SEED = 0
KS = (1, 3, 5)
TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


def _recall(retriever: Callable[[str, int], list[str]], qa: list, k: int) -> float:
    hits = sum(1 for item in qa if set(retriever(item.question, k)) & set(item.source_ids))
    return round(hits / len(qa), 4)


def main() -> None:
    docs = load_corpus()
    qa = [q for q in load_golden_qa() if q.source_ids]
    texts = [d.title + ". " + d.abstract for d in docs]
    ids = [d.arxiv_id for d in docs]
    vecs = hash_embed(texts, dims=DIMS, seed=SEED)
    tokenised = [_tokenize(t) for t in texts]

    bm25 = BM25Okapi(tokenised, k1=1.5, b=0.75)
    bm25_flat = BM25Okapi(tokenised, k1=100.0, b=0.0)  # ≈ TF-IDF

    def dense(q: str, k: int) -> list[str]:
        qv = hash_embed([q], dims=DIMS, seed=SEED)[0]
        idx, _ = cosine_topk(qv, vecs, k=k)
        return [ids[i] for i in idx]

    def bm25_retrieve(q: str, k: int, idx: BM25Okapi = bm25) -> list[str]:
        scores = idx.get_scores(_tokenize(q))
        return [ids[i] for i in np.argsort(-scores)[:k]]

    def tfidf_retrieve(q: str, k: int) -> list[str]:
        return bm25_retrieve(q, k, idx=bm25_flat)

    def rrf(q: str, k: int, rrf_k: int = 60) -> list[str]:
        qv = hash_embed([q], dims=DIMS, seed=SEED)[0]
        dense_order = cosine_topk(qv, vecs, k=len(ids))[0]
        sparse_order = np.argsort(-bm25.get_scores(_tokenize(q)))
        fused: dict[int, float] = {}
        for rank, i in enumerate(dense_order):
            fused[int(i)] = fused.get(int(i), 0.0) + 1.0 / (rrf_k + rank)
        for rank, i in enumerate(sparse_order):
            fused[int(i)] = fused.get(int(i), 0.0) + 1.0 / (rrf_k + rank)
        top = sorted(fused.items(), key=lambda kv: -kv[1])[:k]
        return [ids[i] for i, _ in top]

    def weighted(q: str, k: int, alpha: float = 0.5) -> list[str]:
        qv = hash_embed([q], dims=DIMS, seed=SEED)[0]
        dense_scores = vecs @ qv
        d_min, d_max = float(dense_scores.min()), float(dense_scores.max())
        d_norm = (dense_scores - d_min) / (d_max - d_min + 1e-9)
        bm25_scores = np.asarray(bm25.get_scores(_tokenize(q)), dtype=np.float64)
        b_min, b_max = float(bm25_scores.min()), float(bm25_scores.max())
        b_norm = (bm25_scores - b_min) / (b_max - b_min + 1e-9)
        combined = alpha * d_norm + (1.0 - alpha) * b_norm
        return [ids[i] for i in np.argsort(-combined)[:k]]

    alphas = [round(a, 2) for a in np.linspace(0.0, 1.0, 11).tolist()]
    alpha_recall_at_3 = {
        f"alpha={a:.2f}": _recall(lambda q, k, a=a: weighted(q, k, a), qa, 3) for a in alphas
    }
    alpha_star = max(alpha_recall_at_3, key=lambda a: alpha_recall_at_3[a])
    alpha_star_val = float(alpha_star.split("=")[1])

    per_retriever = {
        "tfidf": {f"recall@{k}": _recall(tfidf_retrieve, qa, k) for k in KS},
        "bm25": {f"recall@{k}": _recall(bm25_retrieve, qa, k) for k in KS},
        "dense": {f"recall@{k}": _recall(dense, qa, k) for k in KS},
        "rrf": {f"recall@{k}": _recall(rrf, qa, k) for k in KS},
        "weighted_best": {
            f"recall@{k}": _recall(lambda q, k, a=alpha_star_val: weighted(q, k, a), qa, k)
            for k in KS
        },
    }

    snapshot = {
        "technique": "bm25-and-hybrid",
        "version": "0.1.0",
        "dataset": "benchmarks/golden-qa/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "n_docs": len(docs),
            "n_questions": len(qa),
            "config": {"bm25_k1": 1.5, "bm25_b": 0.75, "dense_dims": DIMS, "rrf_k": 60},
            "per_retriever": per_retriever,
            "alpha_sweep_recall@3": alpha_recall_at_3,
            "alpha_star": alpha_star_val,
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
