"""Eval for the incremental-indexing leaf.

Models a tiny flat-index lifecycle and reports recall after each mutation:

    1. baseline: build the index over the canonical 10-doc corpus.
    2. tombstone-delete: mark 2 docs deleted (NOT re-built); top-k post-filters.
    3. add-new: insert 2 synthetic docs.
    4. partial-re-embed: re-embed half the corpus with a new seed (= a new
       embedding model) without re-embedding the other half. This produces the
       recall cliff that mixed-embedder indexes exhibit in practice.
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

from shared.embedders import hash_embed  # noqa: E402
from shared.loaders import load_corpus, load_golden_qa  # noqa: E402

DIMS = 256
SEED_OLD = 0
SEED_NEW = 7
K = 3


class FlatIndex:
    """Minimal flat cosine index with online add / tombstone delete."""

    def __init__(self, dims: int) -> None:
        self.dims = dims
        self.vecs: list[np.ndarray] = []
        self.ids: list[str] = []
        self.deleted: set[int] = set()

    def add(self, doc_id: str, vec: np.ndarray) -> int:
        vec = vec / (np.linalg.norm(vec) + 1e-9)
        self.vecs.append(vec)
        self.ids.append(doc_id)
        return len(self.vecs) - 1

    def delete(self, doc_id: str) -> bool:
        try:
            idx = self.ids.index(doc_id)
        except ValueError:
            return False
        self.deleted.add(idx)
        return True

    def replace(self, doc_id: str, vec: np.ndarray) -> bool:
        try:
            idx = self.ids.index(doc_id)
        except ValueError:
            return False
        self.vecs[idx] = vec / (np.linalg.norm(vec) + 1e-9)
        return True

    def search(self, qv: np.ndarray, k: int) -> list[str]:
        if not self.vecs:
            return []
        qv = qv / (np.linalg.norm(qv) + 1e-9)
        matrix = np.stack(self.vecs)
        scores = matrix @ qv
        order = np.argsort(-scores)
        out: list[str] = []
        for i in order:
            i_int = int(i)
            if i_int in self.deleted:
                continue
            out.append(self.ids[i_int])
            if len(out) == k:
                break
        return out


def _recall(idx: FlatIndex, qa: list, embed_q, k: int) -> float:
    hits = sum(
        1 for item in qa if set(idx.search(embed_q(item.question), k)) & set(item.source_ids)
    )
    return round(hits / len(qa), 4)


def main() -> None:
    docs = load_corpus()
    qa = [q for q in load_golden_qa() if q.source_ids]

    def embed_old(text: str) -> np.ndarray:
        return hash_embed([text], dims=DIMS, seed=SEED_OLD)[0]

    def embed_new(text: str) -> np.ndarray:
        return hash_embed([text], dims=DIMS, seed=SEED_NEW)[0]

    # --- 1. baseline ----------------------------------------------------
    idx = FlatIndex(DIMS)
    for d in docs:
        idx.add(d.arxiv_id, embed_old(d.title + ". " + d.abstract))
    baseline_recall = _recall(idx, qa, embed_old, K)

    # --- 2. tombstone delete -------------------------------------------
    to_delete = [docs[0].arxiv_id, docs[2].arxiv_id]
    qa_after_delete = [q for q in qa if not set(q.source_ids).issubset(set(to_delete))]
    for did in to_delete:
        idx.delete(did)
    post_delete_recall = _recall(idx, qa_after_delete, embed_old, K)
    n_live = len(idx.vecs) - len(idx.deleted)

    # --- 3. add new ----------------------------------------------------
    extras = [
        ("synth-101", "Reproducibility study of speculative decoding under fp8 quantisation."),
        ("synth-102", "Survey of retrieval failure modes in legal document QA systems."),
    ]
    for did, text in extras:
        idx.add(did, embed_old(text))
    post_add_recall = _recall(idx, qa_after_delete, embed_old, K)
    n_total = len(idx.vecs) - len(idx.deleted)

    # --- 4. partial re-embed (mixed embedders) -------------------------
    half = len(docs) // 2
    for d in docs[:half]:
        idx.replace(d.arxiv_id, embed_new(d.title + ". " + d.abstract))
    # Queries still embedded with the OLD seed — half the index speaks a
    # different language now. This is the recall cliff.
    mixed_recall = _recall(idx, qa_after_delete, embed_old, K)

    # Sanity: if we also embed queries with the NEW seed, the FIRST half lines
    # up but the second half breaks — verifies the cliff is real, not noise.
    mixed_recall_new_queries = _recall(idx, qa_after_delete, embed_new, K)

    snapshot = {
        "technique": "incremental-indexing",
        "version": "0.1.0",
        "dataset": "benchmarks/golden-qa/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "n_docs": len(docs),
            "n_questions": len(qa),
            "k": K,
            "config": {
                "dims": DIMS,
                "seed_old": SEED_OLD,
                "seed_new": SEED_NEW,
                "deleted_ids": to_delete,
                "added_ids": [did for did, _ in extras],
                "partial_re_embed_count": half,
            },
            "baseline_recall@k": baseline_recall,
            "post_delete_recall@k": post_delete_recall,
            "post_add_recall@k": post_add_recall,
            "mixed_embedder_recall@k_old_queries": mixed_recall,
            "mixed_embedder_recall@k_new_queries": mixed_recall_new_queries,
            "live_docs_post_delete": n_live,
            "live_docs_post_add": n_total,
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
