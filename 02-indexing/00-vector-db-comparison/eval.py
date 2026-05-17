"""Eval for the vector-DB comparison leaf.

Builds Flat / scratch-HNSW / IVF (k-means) / BM25 indexes over the canonical
arxiv corpus and reports ``recall@{1,3,5}`` plus build-time-ms per index.

The implementations mirror the notebook (kept small on purpose). Production
deployments should use FAISS/hnswlib/pgvector/Qdrant.
"""

from __future__ import annotations

import json
import math
import os
import random
import re
import sys
import time
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
from sklearn.cluster import MiniBatchKMeans  # noqa: E402

from shared.embedders import cosine_topk, hash_embed  # noqa: E402
from shared.loaders import load_corpus, load_golden_qa  # noqa: E402

DIMS = 256
SEED = 0
KS = (1, 3, 5)
TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


def _flat_search(vecs: np.ndarray, qv: np.ndarray, k: int) -> np.ndarray:
    idx, _ = cosine_topk(qv, vecs, k=k)
    return idx


def _build_ivf(vecs: np.ndarray, n_clusters: int) -> tuple[MiniBatchKMeans, dict[int, np.ndarray]]:
    n_clusters = min(n_clusters, len(vecs))
    km = MiniBatchKMeans(n_clusters=n_clusters, random_state=0, n_init="auto")
    labels = km.fit_predict(vecs)
    buckets = {c: np.where(labels == c)[0] for c in range(n_clusters)}
    return km, buckets


def _ivf_search(
    km: MiniBatchKMeans,
    buckets: dict[int, np.ndarray],
    vecs: np.ndarray,
    qv: np.ndarray,
    k: int,
    nprobe: int,
) -> np.ndarray:
    qv = qv / (np.linalg.norm(qv) + 1e-9)
    centroid_scores = km.cluster_centers_ @ qv
    top_clusters = np.argsort(-centroid_scores)[: min(nprobe, len(buckets))]
    parts = [buckets[c] for c in top_clusters if c in buckets and len(buckets[c]) > 0]
    if not parts:
        return np.array([], dtype=int)
    cands = np.concatenate(parts)
    scores = vecs[cands] @ qv
    return cands[np.argsort(-scores)[:k]]


class _ScratchHNSW:
    """Minimal layered-graph HNSW following Malkov & Yashunin (2016)."""

    def __init__(self, vecs: np.ndarray, m: int = 4, ef_construction: int = 16, seed: int = 0):
        self.m = m
        self.ef_c = ef_construction
        self.ml = 1.0 / math.log(max(m, 2))
        self.rng = random.Random(seed)
        norm = vecs / (np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-9)
        self.vecs = norm
        self.graphs: list[dict[int, list[int]]] = []
        self.entry: int | None = None
        self.max_layer: int = -1
        for i in range(len(norm)):
            self._add(i)

    def _level(self) -> int:
        return int(-math.log(self.rng.random()) * self.ml)

    def _add(self, node: int) -> None:
        level = self._level()
        while len(self.graphs) <= level:
            self.graphs.append({})
        if self.entry is None:
            self.entry = node
            self.max_layer = level
            for lc in range(level + 1):
                self.graphs[lc][node] = []
            return
        ep: int = self.entry
        for lc in range(self.max_layer, level, -1):
            ep = self._search_layer(self.vecs[node], ep, ef=1, lc=lc)[0]
        for lc in range(min(level, self.max_layer), -1, -1):
            results = self._search_layer(self.vecs[node], ep, ef=self.ef_c, lc=lc)
            m_lc = self.m * 2 if lc == 0 else self.m
            neighbours = results[:m_lc]
            self.graphs[lc][node] = neighbours
            for nb in neighbours:
                self.graphs[lc].setdefault(nb, [])
                self.graphs[lc][nb].append(node)
                if len(self.graphs[lc][nb]) > m_lc:
                    self.graphs[lc][nb] = sorted(
                        self.graphs[lc][nb],
                        key=lambda x, nb=nb: -float(self.vecs[x] @ self.vecs[nb]),
                    )[:m_lc]
            if results:
                ep = results[0]
        if level > self.max_layer:
            self.max_layer = level
            self.entry = node

    def _search_layer(self, q: np.ndarray, ep: int, ef: int, lc: int) -> list[int]:
        visited: set[int] = {ep}
        dynamic: list[tuple[float, int]] = [(-float(self.vecs[ep] @ q), ep)]
        candidates: list[tuple[float, int]] = list(dynamic)
        while candidates:
            candidates.sort()
            score_c, c = candidates.pop(0)
            worst = max(dynamic)[0] if dynamic else float("inf")
            if score_c > worst and len(dynamic) >= ef:
                break
            for nb in self.graphs[lc].get(c, []):
                if nb in visited:
                    continue
                visited.add(nb)
                score_nb = -float(self.vecs[nb] @ q)
                if len(dynamic) < ef or score_nb < worst:
                    candidates.append((score_nb, nb))
                    dynamic.append((score_nb, nb))
                    if len(dynamic) > ef:
                        dynamic.remove(max(dynamic))
                        worst = max(dynamic)[0] if dynamic else float("inf")
        return [n for _, n in sorted(dynamic)]

    def search(self, q: np.ndarray, k: int = 5, ef: int = 16) -> np.ndarray:
        if self.entry is None:
            return np.array([], dtype=int)
        q = q / (np.linalg.norm(q) + 1e-9)
        ep: int = self.entry
        for lc in range(self.max_layer, 0, -1):
            results = self._search_layer(q, ep, ef=1, lc=lc)
            if results:
                ep = results[0]
        results = self._search_layer(q, ep, ef=ef, lc=0)
        return np.array(results[:k], dtype=int)


def _recall(retrieve: Callable[[str, int], list[str]], qa: list, k: int) -> float:
    hits = 0
    for item in qa:
        got = set(retrieve(item.question, k))
        if set(item.source_ids) & got:
            hits += 1
    return round(hits / len(qa), 4)


def main() -> None:
    docs = load_corpus()
    qa = [q for q in load_golden_qa() if q.source_ids]
    texts = [d.title + ". " + d.abstract for d in docs]
    ids = [d.arxiv_id for d in docs]
    vecs = hash_embed(texts, dims=DIMS, seed=SEED)

    t0 = time.perf_counter()
    flat_vecs = vecs / (np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-9)
    build_ms: dict[str, float] = {"flat": (time.perf_counter() - t0) * 1000}

    t0 = time.perf_counter()
    hnsw = _ScratchHNSW(vecs, m=4, ef_construction=16, seed=SEED)
    build_ms["hnsw"] = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    km, buckets = _build_ivf(flat_vecs, n_clusters=3)
    build_ms["ivf"] = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    bm25 = BM25Okapi([_tokenize(t) for t in texts])
    build_ms["bm25"] = (time.perf_counter() - t0) * 1000

    def retrieve_flat(q: str, k: int) -> list[str]:
        qv = hash_embed([q], dims=DIMS, seed=SEED)[0]
        return [ids[i] for i in _flat_search(flat_vecs, qv, k)]

    def retrieve_hnsw(q: str, k: int) -> list[str]:
        qv = hash_embed([q], dims=DIMS, seed=SEED)[0]
        return [ids[i] for i in hnsw.search(qv, k=k, ef=16)]

    def retrieve_ivf(q: str, k: int) -> list[str]:
        qv = hash_embed([q], dims=DIMS, seed=SEED)[0]
        return [ids[i] for i in _ivf_search(km, buckets, flat_vecs, qv, k, nprobe=2)]

    def retrieve_bm25(q: str, k: int) -> list[str]:
        scores = bm25.get_scores(_tokenize(q))
        return [ids[i] for i in np.argsort(-scores)[:k]]

    per_index: dict[str, dict[str, float]] = {
        "flat": {f"recall@{k}": _recall(retrieve_flat, qa, k) for k in KS},
        "hnsw": {f"recall@{k}": _recall(retrieve_hnsw, qa, k) for k in KS},
        "ivf": {f"recall@{k}": _recall(retrieve_ivf, qa, k) for k in KS},
        "bm25": {f"recall@{k}": _recall(retrieve_bm25, qa, k) for k in KS},
    }
    for name, ms in build_ms.items():
        per_index[name]["build_ms"] = round(ms, 3)

    snapshot = {
        "technique": "vector-db-comparison",
        "version": "0.1.0",
        "dataset": "benchmarks/golden-qa/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "n_docs": len(docs),
            "n_questions": len(qa),
            "per_index": per_index,
            "config": {"dims": DIMS, "ivf_nlist": 3, "ivf_nprobe": 2, "hnsw_M": 4, "hnsw_ef": 16},
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
