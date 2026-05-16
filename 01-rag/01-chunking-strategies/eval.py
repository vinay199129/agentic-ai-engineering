"""Eval for the four chunking strategies.

The notebook compares strategies on a single sample abstract for clarity; this
script runs them across the *full* corpus and records the structural stats
(avg / max chunks, avg / max chunk chars) per strategy. These are descriptive
metrics — a downstream retrieval eval is what actually proves chunking gains
(see ``01-rag/00-naive-rag/eval.py`` for the retrieval baseline).

Run from the repo root:

    uv run python 01-rag/01-chunking-strategies/eval.py
"""

from __future__ import annotations

import json
import os
import re
import statistics
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
from shared.loaders import load_corpus  # noqa: E402

SEPARATORS = ["\n\n", "\n", ". ", " "]


def chunk_fixed(text: str, size: int = 240, overlap: int = 40) -> list[str]:
    step = size - overlap
    return [text[i : i + size] for i in range(0, max(1, len(text) - overlap), step)]


def chunk_recursive(text: str, target: int = 240, seps: list[str] | None = None) -> list[str]:
    seps = SEPARATORS if seps is None else seps
    if len(text) <= target or not seps:
        return [text]
    sep, rest = seps[0], seps[1:]
    pieces = text.split(sep)
    out: list[str] = []
    buf = ""
    for p in pieces:
        candidate = (buf + sep + p) if buf else p
        if len(candidate) <= target:
            buf = candidate
        else:
            if buf:
                out.append(buf)
            if len(p) <= target:
                buf = p
            else:
                out.extend(chunk_recursive(p, target, rest))
                buf = ""
    if buf:
        out.append(buf)
    return out


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def chunk_semantic(text: str, percentile: float = 60.0) -> list[str]:
    sents = split_sentences(text)
    if len(sents) <= 1:
        return sents
    vecs = hash_embed(sents, dims=256)
    dists = 1.0 - np.sum(vecs[:-1] * vecs[1:], axis=1)
    threshold = float(np.percentile(dists, percentile))
    out: list[str] = []
    current = [sents[0]]
    for s, d in zip(sents[1:], dists, strict=False):
        if d > threshold:
            out.append(" ".join(current))
            current = [s]
        else:
            current.append(s)
    out.append(" ".join(current))
    return out


def chunk_propositional_proxy(text: str) -> list[str]:
    return split_sentences(text)


STRATEGIES = {
    "fixed": chunk_fixed,
    "recursive": chunk_recursive,
    "semantic": chunk_semantic,
    "propositional_proxy": chunk_propositional_proxy,
}


def main() -> None:
    docs = load_corpus()
    metrics: dict[str, float | int | dict[str, float | int]] = {"n_docs": len(docs)}
    per_strategy: dict[str, dict[str, float | int]] = {}
    for name, fn in STRATEGIES.items():
        counts = [len(fn(d.abstract)) for d in docs]
        sizes = [len(c) for d in docs for c in fn(d.abstract)]
        per_strategy[name] = {
            "avg_chunks_per_doc": round(statistics.mean(counts), 3),
            "max_chunks_per_doc": max(counts),
            "avg_chunk_chars": round(statistics.mean(sizes), 2),
            "max_chunk_chars": max(sizes),
            "total_chunks": sum(counts),
        }
    metrics["per_strategy"] = per_strategy

    snapshot = {
        "technique": "chunking-strategies",
        "version": "0.1.0",
        "dataset": "benchmarks/corpus/metadata.jsonl",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": metrics,
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
