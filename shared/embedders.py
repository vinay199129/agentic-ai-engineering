"""Lightweight embedders.

The :func:`hash_embed` function is a deterministic, offline-friendly embedder
used in notebooks and evals so results are reproducible without an API key.
It is **not** competitive with real neural embedders — it is a pedagogical
stand-in that demonstrates the bi-encoder retrieval pattern. Each leaf that
uses it documents how to swap in a real provider via :func:`shared.llm.embed`.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence

import numpy as np

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def hash_embed(
    texts: Sequence[str],
    *,
    dims: int = 256,
    seed: int = 0,
    ngram: tuple[int, int] = (1, 2),
) -> np.ndarray:
    """Deterministic hashing embedder, L2-normalized. Returns shape ``(len(texts), dims)``.

    Each token (and n-gram thereof) hashes to a single coordinate; its sign is
    determined by a second hash so cancellations are possible (similar to the
    feature hashing trick used in scikit-learn's :class:`HashingVectorizer`).
    The ``seed`` parameter shifts the hash so calling with different seeds
    simulates "different embedders" for the embedding-comparison leaf.
    """
    if dims <= 0:
        raise ValueError("dims must be positive")
    n_min, n_max = ngram
    if n_min < 1 or n_max < n_min:
        raise ValueError("ngram must be (n_min, n_max) with 1 <= n_min <= n_max")

    salt = f"|seed={seed}|".encode()
    out = np.zeros((len(texts), dims), dtype=np.float32)

    for row, text in enumerate(texts):
        toks = _tokens(text)
        for n in range(n_min, n_max + 1):
            for i in range(len(toks) - n + 1):
                token = " ".join(toks[i : i + n]).encode()
                h = hashlib.blake2b(token + salt, digest_size=8).digest()
                idx = int.from_bytes(h[:4], "little") % dims
                sign = 1.0 if (h[4] & 1) == 0 else -1.0
                out[row, idx] += sign

        norm = float(np.linalg.norm(out[row]))
        if norm > 0.0:
            out[row] /= norm

    return out


def cosine_topk(query: np.ndarray, matrix: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (indices, scores) of the top-k rows of ``matrix`` by cosine similarity.

    ``query`` and ``matrix`` are assumed L2-normalized.
    """
    if query.ndim != 1:
        raise ValueError("query must be 1-D")
    scores = matrix @ query
    k = min(k, matrix.shape[0])
    idx = np.argpartition(-scores, k - 1)[:k]
    idx = idx[np.argsort(-scores[idx])]
    return idx, scores[idx]


__all__ = ["cosine_topk", "hash_embed"]
