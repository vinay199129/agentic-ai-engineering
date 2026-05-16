"""Tests for shared.embedders."""

from __future__ import annotations

import numpy as np

from shared.embedders import cosine_topk, hash_embed


def test_hash_embed_shape_and_norm() -> None:
    vecs = hash_embed(["hello world", "another doc"], dims=128)
    assert vecs.shape == (2, 128)
    norms = np.linalg.norm(vecs, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-6)


def test_hash_embed_is_deterministic() -> None:
    a = hash_embed(["repeatable text"], dims=64, seed=7)
    b = hash_embed(["repeatable text"], dims=64, seed=7)
    assert np.array_equal(a, b)


def test_hash_embed_seed_changes_vectors() -> None:
    a = hash_embed(["seed test"], dims=64, seed=0)
    b = hash_embed(["seed test"], dims=64, seed=1)
    assert not np.allclose(a, b)


def test_cosine_topk_orders_by_similarity() -> None:
    docs = hash_embed(
        [
            "mixture of experts routing",
            "translation between languages",
            "speculative decoding draft",
        ],
        dims=128,
    )
    q = hash_embed(["mixture of experts router"], dims=128)[0]
    idx, scores = cosine_topk(q, docs, k=2)
    assert idx[0] == 0
    assert scores[0] >= scores[1]


def test_hash_embed_empty_string_returns_zero_vector() -> None:
    vecs = hash_embed([""], dims=32)
    assert vecs.shape == (1, 32)
    assert np.allclose(vecs[0], 0.0)
