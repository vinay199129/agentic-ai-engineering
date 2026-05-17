"""Eval for the HNSW deep-dive leaf.

Sweeps ``ef_search`` and reports the fraction of HNSW top-k that overlaps the
flat (exact) top-k — i.e. recall vs. ground truth, not against the golden Q&A.
This is the metric a vector DB operator actually cares about when tuning
HNSW: "how much recall am I trading away for latency at this ef?"
"""

from __future__ import annotations

import json
import math
import os
import random
import sys
import time
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

DIMS = 64
SEED = 0
EF_SWEEP = (1, 2, 4, 8, 16)
K = 5


class HNSW:
    """Pure-numpy HNSW following Malkov & Yashunin (2016) Algorithm 1."""

    def __init__(self, m: int = 4, ef_construction: int = 16, seed: int = 0):
        self.m = m
        self.ef_c = ef_construction
        self.ml = 1.0 / math.log(max(m, 2))
        self.rng = random.Random(seed)
        self.vecs: list[np.ndarray] = []
        self.graphs: list[dict[int, list[int]]] = []
        self.entry: int | None = None
        self.max_layer: int = -1

    def _level(self) -> int:
        return int(-math.log(self.rng.random()) * self.ml)

    def _search_layer(self, q: np.ndarray, ep: int, ef: int, lc: int) -> list[int]:
        visited: set[int] = {ep}
        candidates: list[tuple[float, int]] = [(-float(self.vecs[ep] @ q), ep)]
        dynamic: list[tuple[float, int]] = list(candidates)
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

    def add(self, vec: np.ndarray) -> int:
        node = len(self.vecs)
        v = vec / (np.linalg.norm(vec) + 1e-9)
        self.vecs.append(v)
        level = self._level()
        while len(self.graphs) <= level:
            self.graphs.append({})
        if self.entry is None:
            self.entry = node
            self.max_layer = level
            for lc in range(level + 1):
                self.graphs[lc][node] = []
            return node
        ep: int = self.entry
        for lc in range(self.max_layer, level, -1):
            results = self._search_layer(v, ep, ef=1, lc=lc)
            if results:
                ep = results[0]
        for lc in range(min(level, self.max_layer), -1, -1):
            results = self._search_layer(v, ep, ef=self.ef_c, lc=lc)
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
        return node

    def search(self, q: np.ndarray, k: int = 5, ef: int = 16) -> list[int]:
        if self.entry is None:
            return []
        q = q / (np.linalg.norm(q) + 1e-9)
        ep: int = self.entry
        for lc in range(self.max_layer, 0, -1):
            results = self._search_layer(q, ep, ef=1, lc=lc)
            if results:
                ep = results[0]
        return self._search_layer(q, ep, ef=ef, lc=0)[:k]


def main() -> None:
    random.seed(SEED)
    np.random.seed(SEED)
    docs = load_corpus()
    qa = [q for q in load_golden_qa() if q.source_ids]
    texts = [d.title + ". " + d.abstract for d in docs]
    vecs = hash_embed(texts, dims=DIMS, seed=SEED)

    t0 = time.perf_counter()
    h = HNSW(m=4, ef_construction=16, seed=SEED)
    for v in vecs:
        h.add(v)
    build_ms = (time.perf_counter() - t0) * 1000

    recall_by_ef: dict[str, float] = {}
    latency_us_by_ef: dict[str, float] = {}
    for ef in EF_SWEEP:
        total_overlap = 0.0
        t0 = time.perf_counter()
        for item in qa:
            qv = hash_embed([item.question], dims=DIMS, seed=SEED)[0]
            flat_top = set(cosine_topk(qv, vecs, k=K)[0].tolist())
            hnsw_top = set(h.search(qv, k=K, ef=ef))
            total_overlap += len(flat_top & hnsw_top) / max(len(flat_top), 1)
        latency_us_by_ef[f"ef={ef}"] = round(((time.perf_counter() - t0) * 1e6) / len(qa), 2)
        recall_by_ef[f"ef={ef}"] = round(total_overlap / len(qa), 4)

    graph_stats = {
        "n_layers": len(h.graphs),
        "max_layer": h.max_layer,
        "avg_degree_layer0": round(
            float(np.mean([len(nb) for nb in h.graphs[0].values()])) if h.graphs else 0.0, 3
        ),
        "build_ms": round(build_ms, 3),
    }

    snapshot = {
        "technique": "hnsw-deep-dive",
        "version": "0.1.0",
        "dataset": "benchmarks/golden-qa/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "n_docs": len(docs),
            "n_questions": len(qa),
            "k": K,
            "config": {"M": 4, "ef_construction": 16, "dims": DIMS},
            "recall_vs_flat": recall_by_ef,
            "query_latency_us": latency_us_by_ef,
            "graph": graph_stats,
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
