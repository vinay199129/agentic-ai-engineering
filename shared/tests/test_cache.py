"""Tests for shared.cache."""

from __future__ import annotations

from pathlib import Path

import pytest

from shared.cache import CacheMissError, JSONLCache, stable_key


def test_stable_key_is_order_independent() -> None:
    a = stable_key({"model": "x", "messages": [{"role": "user", "content": "hi"}]})
    b = stable_key({"messages": [{"role": "user", "content": "hi"}], "model": "x"})
    assert a == b


def test_stable_key_differs_on_different_payloads() -> None:
    assert stable_key({"a": 1}) != stable_key({"a": 2})


def test_jsonl_cache_roundtrip(tmp_path: Path) -> None:
    cache = JSONLCache(namespace="t", root=tmp_path)
    assert cache.get("missing") is None
    cache.set("k1", {"hello": "world"})
    assert cache.get("k1") == {"hello": "world"}

    fresh = JSONLCache(namespace="t", root=tmp_path)
    assert fresh.get("k1") == {"hello": "world"}
    assert len(fresh) == 1
    assert "k1" in fresh


def test_jsonl_cache_dedupes_identical_writes(tmp_path: Path) -> None:
    cache = JSONLCache(namespace="t", root=tmp_path)
    cache.set("k1", [1, 2, 3])
    cache.set("k1", [1, 2, 3])
    lines = cache.path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1


def test_jsonl_cache_last_write_wins(tmp_path: Path) -> None:
    cache = JSONLCache(namespace="t", root=tmp_path)
    cache.set("k1", "first")
    cache.set("k1", "second")
    fresh = JSONLCache(namespace="t", root=tmp_path)
    assert fresh.get("k1") == "second"


def test_lookup_or_raise(tmp_path: Path) -> None:
    cache = JSONLCache(namespace="t", root=tmp_path)
    with pytest.raises(CacheMissError):
        cache.lookup_or_raise("nope")
    cache.set("yep", 42)
    assert cache.lookup_or_raise("yep") == 42
