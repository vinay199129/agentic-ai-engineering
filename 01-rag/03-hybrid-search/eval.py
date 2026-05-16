"""Eval for hybrid search vs dense vs BM25 baselines."""

from __future__ import annotations

import json
import os
import re
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

from rank_bm25 import BM25Okapi  # noqa: E402

from shared.embedders import cosine_topk, hash_embed  # noqa: E402
from shared.loaders import load_corpus, load_golden_qa  # noqa: E402

DIMS = 256
SEED = 0
KS = (1, 3, 5)
TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def tokenize(t: str) -> list[str]:
    return [w.lower() for w in TOKEN_RE.findall(t)]


def main() -> None:
    docs = load_corpus()
    qa = [q for q in load_golden_qa() if q.source_ids]
    doc_texts = [d.title + ". " + d.abstract for d in docs]
    doc_ids = [d.arxiv_id for d in docs]
    doc_vecs = hash_embed(doc_texts, dims=DIMS, seed=SEED)
    bm25 = BM25Okapi([tokenize(t) for t in doc_texts])

    def retrieve_dense(q: str, k: int) -> list[str]:
        qv = hash_embed([q], dims=DIMS, seed=SEED)[0]
        idx, _ = cosine_topk(qv, doc_vecs, k=k)
        return [doc_ids[i] for i in idx]

    def retrieve_bm25(q: str, k: int) -> list[str]:
        scores = bm25.get_scores(tokenize(q))
        order = np.argsort(-scores)[:k]
        return [doc_ids[i] for i in order]

    def retrieve_hybrid(q: str, k: int, rrf_k: int = 60) -> list[str]:
        dense = retrieve_dense(q, k=len(doc_ids))
        sparse = retrieve_bm25(q, k=len(doc_ids))
        fused: dict[str, float] = {}
        for rank, doc in enumerate(dense):
            fused[doc] = fused.get(doc, 0.0) + 1.0 / (rrf_k + rank)
        for rank, doc in enumerate(sparse):
            fused[doc] = fused.get(doc, 0.0) + 1.0 / (rrf_k + rank)
        return [d for d, _ in sorted(fused.items(), key=lambda kv: -kv[1])[:k]]

    def recall(retriever, k: int) -> float:
        hits = 0
        for item in qa:
            got = set(retriever(item.question, k))
            if set(item.source_ids) & got:
                hits += 1
        return round(hits / len(qa), 4)

    per = {
        "dense": {f"recall@{k}": recall(retrieve_dense, k) for k in KS},
        "bm25": {f"recall@{k}": recall(retrieve_bm25, k) for k in KS},
        "hybrid_rrf": {f"recall@{k}": recall(retrieve_hybrid, k) for k in KS},
    }
    snapshot = {
        "technique": "hybrid-search",
        "version": "0.1.0",
        "dataset": "benchmarks/golden-qa/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {"n_docs": len(docs), "n_questions": len(qa), "per_retriever": per},
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
