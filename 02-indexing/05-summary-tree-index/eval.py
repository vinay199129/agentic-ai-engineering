"""Eval for the summary-tree index leaf.

Reports tree-retrieve vs flat-retrieve ``recall@3`` plus the cluster shape.
Uses cached leaf summaries (``LLM_CACHE_ONLY=1`` is the default in CI). If a
summary isn't cached, falls back to the first 240 characters of the abstract
so the snapshot is always reproducible.
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

if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
    os.environ.setdefault("LLM_CACHE_ONLY", "1")

from sklearn.cluster import KMeans  # noqa: E402

from shared.embedders import cosine_topk, hash_embed  # noqa: E402
from shared.llm import Message, complete  # noqa: E402
from shared.loaders import load_corpus, load_golden_qa  # noqa: E402

MODEL = "openai/gpt-4o-mini"
NS = "02-indexing/05-summary-tree-index"
N_CLUSTERS = 3
DIMS = 256
SEED = 0
K = 3

LEAF_SYS = (
    "Summarize the following research abstract in 1-2 crisp sentences. "
    "Include the method name, the key result (one metric), and the problem solved. "
    "Output ONLY the summary, no preamble."
)


def _leaf_summary(abstract: str) -> str:
    try:
        return complete(
            model=MODEL,
            namespace=NS,
            messages=[
                Message(role="system", content=LEAF_SYS),
                Message(role="user", content=abstract),
            ],
        ).content
    except Exception:
        # Deterministic fallback — first 240 chars of the abstract.
        return abstract[:240]


def main() -> None:
    docs = load_corpus()
    qa = [q for q in load_golden_qa() if q.source_ids]
    doc_ids = [d.arxiv_id for d in docs]

    leaf_sums = {d.arxiv_id: _leaf_summary(d.abstract) for d in docs}
    sum_texts = [leaf_sums[d.arxiv_id] for d in docs]
    sum_vecs = hash_embed(sum_texts, dims=DIMS, seed=SEED)

    n_clusters = min(N_CLUSTERS, len(docs))
    km = KMeans(n_clusters=n_clusters, random_state=SEED, n_init="auto")
    labels = km.fit_predict(sum_vecs)
    clusters = {
        i: [doc_ids[j] for j, lbl in enumerate(labels) if lbl == i] for i in range(n_clusters)
    }
    cluster_sizes = {f"cluster_{i}": len(members) for i, members in clusters.items()}

    # Cluster-level vector is the centroid summary embedding.
    cluster_vecs = km.cluster_centers_

    def tree_retrieve(question: str, k: int) -> list[str]:
        qv = hash_embed([question], dims=DIMS, seed=SEED)[0]
        cidx, _ = cosine_topk(qv, cluster_vecs, k=1)
        best = int(cidx[0])
        members = clusters[best]
        if not members:
            return []
        member_vecs = hash_embed([leaf_sums[did] for did in members], dims=DIMS, seed=SEED)
        leaf_idx, _ = cosine_topk(qv, member_vecs, k=min(k, len(members)))
        return [members[int(i)] for i in leaf_idx]

    def flat_retrieve(question: str, k: int) -> list[str]:
        qv = hash_embed([question], dims=DIMS, seed=SEED)[0]
        idx, _ = cosine_topk(qv, sum_vecs, k=k)
        return [doc_ids[int(i)] for i in idx]

    def recall(retrieve, k: int) -> float:
        hits = sum(1 for q in qa if set(retrieve(q.question, k)) & set(q.source_ids))
        return round(hits / len(qa), 4)

    snapshot = {
        "technique": "summary-tree-index",
        "version": "0.1.0",
        "dataset": "benchmarks/golden-qa/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "n_docs": len(docs),
            "n_questions": len(qa),
            "k": K,
            "config": {"n_clusters": n_clusters, "dims": DIMS},
            "tree_recall@k": recall(tree_retrieve, K),
            "flat_recall@k": recall(flat_retrieve, K),
            "cluster_sizes": cluster_sizes,
            "avg_summary_len_chars": int(np.mean([len(s) for s in sum_texts])),
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
