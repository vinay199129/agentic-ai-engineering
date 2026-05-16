"""Cross-provider LLM shim built on :mod:`litellm` with deterministic caching.

Usage
-----
.. code-block:: python

    from shared.llm import complete, Message

    reply = complete(
        model="openai/gpt-4o-mini",
        messages=[Message(role="user", content="Hello!")],
        namespace="00-foundations/01-structured-outputs",
    )
    print(reply.content)

Behavior matrix
---------------
======================== ==================== =====================================
``LLM_CACHE_ONLY`` flag   Cache hit?           Result
======================== ==================== =====================================
unset / 0                 yes                  Return cached response (no API call)
unset / 0                 no                   Call provider, cache, return
1 / true                  yes                  Return cached response
1 / true                  no                   Raise :class:`CacheMissError`
======================== ==================== =====================================

This keeps notebooks runnable offline in CI while still letting local users
populate the cache against real providers.

Embeddings use the same backend via :func:`embed`; the cache value is the raw
``list[float]`` so it stays diff-friendly in JSONL form.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from typing import Any, Literal

from pydantic import BaseModel, Field

from .cache import JSONLCache, cache_only_mode, stable_key

Role = Literal["system", "user", "assistant", "tool"]


class Message(BaseModel):
    """Single chat message. Mirrors OpenAI's ``ChatCompletionMessageParam``."""

    role: Role
    content: str
    name: str | None = None
    tool_call_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.name is not None:
            out["name"] = self.name
        if self.tool_call_id is not None:
            out["tool_call_id"] = self.tool_call_id
        return out


class ToolSpec(BaseModel):
    """OpenAI-style tool/function spec passed straight to litellm."""

    name: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)

    def to_openai(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: str


class Completion(BaseModel):
    content: str
    model: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    finish_reason: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


# --- internals ------------------------------------------------------------


def _request_payload(
    *,
    model: str,
    messages: Sequence[Message],
    tools: Sequence[ToolSpec] | None,
    temperature: float,
    max_tokens: int | None,
    response_format: dict[str, Any] | None,
    extra: dict[str, Any] | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "messages": [m.to_dict() for m in messages],
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if tools:
        payload["tools"] = [t.to_openai() for t in tools]
    if response_format is not None:
        payload["response_format"] = response_format
    if extra:
        for k, v in extra.items():
            payload[k] = v
    return payload


def _normalize_response(resp: Any) -> Completion:
    """Convert a litellm/OpenAI ChatCompletion-like object to :class:`Completion`."""
    choice = resp.choices[0]
    msg = choice.message
    content = getattr(msg, "content", None) or ""
    tool_calls: list[ToolCall] = []
    for tc in getattr(msg, "tool_calls", None) or []:
        fn = getattr(tc, "function", None)
        tool_calls.append(
            ToolCall(
                id=getattr(tc, "id", ""),
                name=getattr(fn, "name", ""),
                arguments=getattr(fn, "arguments", "") or "",
            )
        )
    raw: dict[str, Any] = {}
    if hasattr(resp, "model_dump"):
        try:
            raw = resp.model_dump()
        except Exception:  # pragma: no cover - defensive
            raw = {}
    return Completion(
        content=content,
        model=getattr(resp, "model", "") or "",
        tool_calls=tool_calls,
        finish_reason=getattr(choice, "finish_reason", None),
        raw=raw,
    )


def _completion_from_cached(value: Any) -> Completion:
    if isinstance(value, dict) and "content" in value:
        return Completion.model_validate(value)
    # Backwards-compat: a plain string response cached directly.
    return Completion(content=str(value), model="cache")


# --- public API -----------------------------------------------------------


def complete(
    *,
    model: str,
    messages: Sequence[Message],
    namespace: str,
    tools: Sequence[ToolSpec] | None = None,
    temperature: float = 0.0,
    max_tokens: int | None = None,
    response_format: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> Completion:
    """Run a chat completion with deterministic caching.

    ``namespace`` selects which on-disk cache file is used. By convention pass
    the leaf folder path (e.g. ``"00-foundations/01-structured-outputs"``) so
    a notebook's cache travels with the notebook.
    """
    payload = _request_payload(
        model=model,
        messages=messages,
        tools=tools,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=response_format,
        extra=extra,
    )
    cache = JSONLCache(namespace=namespace)
    key = stable_key({"kind": "chat", **payload})

    hit = cache.get(key)
    if hit is not None:
        return _completion_from_cached(hit)

    if cache_only_mode():
        cache.lookup_or_raise(key)  # always raises here

    # Lazy import so the package itself stays importable without litellm.
    import litellm

    resp = litellm.completion(**payload)
    norm = _normalize_response(resp)
    cache.set(key, norm.model_dump())
    return norm


def embed(
    *,
    model: str,
    inputs: Sequence[str],
    namespace: str,
    extra: dict[str, Any] | None = None,
) -> list[list[float]]:
    """Embed inputs with deterministic caching. One cache entry per input."""
    cache = JSONLCache(namespace=namespace)
    results: list[list[float] | None] = [None] * len(inputs)
    missing: list[tuple[int, str, str]] = []

    for i, text in enumerate(inputs):
        key = stable_key({"kind": "embed", "model": model, "input": text, "extra": extra or {}})
        cached = cache.get(key)
        if cached is not None:
            results[i] = list(cached)
        else:
            missing.append((i, key, text))

    if missing:
        if cache_only_mode():
            # Surface the first miss for a clear error.
            cache.lookup_or_raise(missing[0][1])

        import litellm

        texts = [m[2] for m in missing]
        kwargs: dict[str, Any] = {"model": model, "input": texts}
        if extra:
            kwargs.update(extra)
        resp = litellm.embedding(**kwargs)
        # litellm returns OpenAI-shaped {data:[{embedding:[...]}, ...]}
        for (idx, key, _text), datum in zip(missing, resp.data, strict=True):
            vec: list[float] = (
                list(datum["embedding"]) if isinstance(datum, dict) else list(datum.embedding)
            )
            cache.set(key, vec)
            results[idx] = vec

    assert all(r is not None for r in results), "embedding cache fill incomplete"
    return [list(r) for r in results if r is not None]


def have_api_key(provider: str) -> bool:
    """Best-effort check for whether a provider's API key is configured."""
    env = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "cohere": "COHERE_API_KEY",
        "groq": "GROQ_API_KEY",
        "together": "TOGETHER_API_KEY",
        "voyage": "VOYAGE_API_KEY",
    }.get(provider.lower())
    return bool(env and os.getenv(env))


__all__ = [
    "Completion",
    "Message",
    "ToolCall",
    "ToolSpec",
    "complete",
    "embed",
    "have_api_key",
]
