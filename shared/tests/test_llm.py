"""Tests for shared.llm focusing on the cache-only path (no live calls)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shared.cache import CacheMissError, JSONLCache, stable_key
from shared.llm import Completion, Message, complete, embed


def _seed_chat_cache(tmp_path: Path, *, model: str, content: str) -> None:
    payload = {
        "kind": "chat",
        "model": model,
        "messages": [{"role": "user", "content": "hi"}],
        "temperature": 0.0,
    }
    key = stable_key(payload)
    JSONLCache(namespace="unit", root=tmp_path).set(
        key,
        Completion(content=content, model=model).model_dump(),
    )


def test_complete_returns_cached(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LLM_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("LLM_CACHE_ONLY", "1")
    _seed_chat_cache(tmp_path, model="openai/gpt-4o-mini", content="cached!")

    out = complete(
        model="openai/gpt-4o-mini",
        messages=[Message(role="user", content="hi")],
        namespace="unit",
    )
    assert out.content == "cached!"


def test_complete_raises_on_miss(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LLM_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("LLM_CACHE_ONLY", "1")
    with pytest.raises(CacheMissError):
        complete(
            model="openai/gpt-4o-mini",
            messages=[Message(role="user", content="nope")],
            namespace="unit",
        )


def test_embed_returns_cached(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LLM_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("LLM_CACHE_ONLY", "1")

    model = "openai/text-embedding-3-small"
    cache = JSONLCache(namespace="unit", root=tmp_path)
    for text, vec in [("a", [0.1, 0.2]), ("b", [0.3, 0.4])]:
        key = stable_key({"kind": "embed", "model": model, "input": text, "extra": {}})
        cache.set(key, vec)

    vecs = embed(model=model, inputs=["a", "b"], namespace="unit")
    assert vecs == [[0.1, 0.2], [0.3, 0.4]]


def test_embed_raises_on_partial_miss(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LLM_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("LLM_CACHE_ONLY", "1")

    model = "openai/text-embedding-3-small"
    cache = JSONLCache(namespace="unit", root=tmp_path)
    key = stable_key({"kind": "embed", "model": model, "input": "a", "extra": {}})
    cache.set(key, [0.1, 0.2])

    with pytest.raises(CacheMissError):
        embed(model=model, inputs=["a", "missing"], namespace="unit")


def test_message_serialization_round_trip() -> None:
    m = Message(role="user", content="hi", name=None, tool_call_id=None)
    d = m.to_dict()
    assert d == {"role": "user", "content": "hi"}
    parsed = json.loads(json.dumps(d))
    assert parsed == d
