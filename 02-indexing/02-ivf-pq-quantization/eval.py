"""Eval for IVF + PQ quantization.

Reports:
    - per-``nprobe`` IVF recall against the golden Q&A
    - PQ approximation recall (ADC) against the golden Q&A
    - memory ratio: original float32 vectors vs PQ codes
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

from sklearn.cluster import MiniBatchKMeans  # noqa: E402

from shared.embedders import cosine_topk, hash_embed  # noqa: E402
from shared.loaders import load_corpus, load_golden_qa  # noqa: E402

DIMS = 256
SEED = 0
K = 3
NLIST = 3


class IVFFlat:
    def __init__(self, vecs: np.ndarray, nlist: int) -> None:
        nlist = min(nlist, len(vecs))
        self.norm = vecs / (np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-9)
        self.km = MiniBatchKMeans(n_clusters=nlist, random_state=0, n_init="auto")
        self.assign = self.km.fit_predict(self.norm)
        self.buckets = {c: np.where(self.assign == c)[0] for c in range(nlist)}
        self.nlist = nlist

    def search(self, qv: np.ndarray, k: int, nprobe: int) -> np.ndarray:
        qv = qv / (np.linalg.norm(qv) + 1e-9)
        cent_scores = self.km.cluster_centers_ @ qv
        probed = np.argsort(-cent_scores)[: min(nprobe, self.nlist)]
        parts = [self.buckets[c] for c in probed if len(self.buckets[c]) > 0]
        if not parts:
            return np.array([], dtype=int)
        cands = np.concatenate(parts)
        scores = self.norm[cands] @ qv
        return cands[np.argsort(-scores)[:k]]


class ProductQuantizer:
    def __init__(self, vecs: np.ndarray, m: int, k_star: int) -> None:
        if vecs.shape[1] % m != 0:
            raise ValueError("dims must be divisible by m")
        self.m = m
        self.k = min(k_star, len(vecs))
        self.d_sub = vecs.shape[1] // m
        self.codebooks: list[np.ndarray] = []
        self.codes = np.zeros((len(vecs), m), dtype=np.uint8)
        for i in range(m):
            sub = vecs[:, i * self.d_sub : (i + 1) * self.d_sub].astype(np.float32)
            km = MiniBatchKMeans(n_clusters=self.k, random_state=i, n_init="auto")
            km.fit(sub)
            self.codebooks.append(km.cluster_centers_)
            self.codes[:, i] = km.predict(sub).astype(np.uint8)

    def approx_scores(self, qv: np.ndarray) -> np.ndarray:
        scores = np.zeros(len(self.codes), dtype=np.float32)
        for i in range(self.m):
            sub_q = qv[i * self.d_sub : (i + 1) * self.d_sub].astype(np.float32)
            table = self.codebooks[i] @ sub_q
            scores += table[self.codes[:, i]]
        return scores


def _recall(retrieved_ids: list[set[str]], qa: list) -> float:
    hits = sum(1 for got, item in zip(retrieved_ids, qa, strict=True) if got & set(item.source_ids))
    return round(hits / len(qa), 4)


def main() -> None:
    docs = load_corpus()
    qa = [q for q in load_golden_qa() if q.source_ids]
    texts = [d.title + ". " + d.abstract for d in docs]
    ids = [d.arxiv_id for d in docs]
    vecs = hash_embed(texts, dims=DIMS, seed=SEED)

    ivf = IVFFlat(vecs, nlist=NLIST)
    pq = ProductQuantizer(vecs, m=8, k_star=4)

    flat_ids = []
    for item in qa:
        qv = hash_embed([item.question], dims=DIMS, seed=SEED)[0]
        idx, _ = cosine_topk(qv, vecs, k=K)
        flat_ids.append({ids[i] for i in idx})
    flat_recall = _recall(flat_ids, qa)

    nprobe_recall: dict[str, float] = {}
    for nprobe in (1, 2, NLIST):
        got_lists: list[set[str]] = []
        for item in qa:
            qv = hash_embed([item.question], dims=DIMS, seed=SEED)[0]
            got_lists.append({ids[i] for i in ivf.search(qv, k=K, nprobe=nprobe)})
        nprobe_recall[f"nprobe={nprobe}"] = _recall(got_lists, qa)

    pq_lists: list[set[str]] = []
    for item in qa:
        qv = hash_embed([item.question], dims=DIMS, seed=SEED)[0]
        scores = pq.approx_scores(qv)
        top = np.argsort(-scores)[:K]
        pq_lists.append({ids[i] for i in top})
    pq_recall = _recall(pq_lists, qa)

    memory = {
        "float32_bytes": int(vecs.nbytes),
        "pq_code_bytes": int(pq.codes.nbytes),
        "codebook_bytes": int(sum(cb.nbytes for cb in pq.codebooks)),
        "compression_ratio_codes_only": round(vecs.nbytes / max(pq.codes.nbytes, 1), 2),
    }

    snapshot = {
        "technique": "ivf-pq-quantization",
        "version": "0.1.0",
        "dataset": "benchmarks/golden-qa/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "n_docs": len(docs),
            "n_questions": len(qa),
            "k": K,
            "config": {"dims": DIMS, "ivf_nlist": NLIST, "pq_m": 8, "pq_k_star": 4},
            "flat_recall@k": flat_recall,
            "ivf_recall@k": nprobe_recall,
            "pq_recall@k": pq_recall,
            "memory": memory,
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
