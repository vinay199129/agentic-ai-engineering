"""Deterministic on-disk cache for LLM and embedding calls.

Design goals
------------
* **Deterministic key.** A stable SHA-256 over a normalized JSON payload —
  identical inputs always produce the same key regardless of dict ordering.
* **Append-only JSONL backend.** One file per *namespace* (typically one per
  notebook). Easy to diff in PRs, easy to ship alongside a notebook so CI can
  replay without hitting live providers.
* **Cache-only mode.** When the ``LLM_CACHE_ONLY`` env var is truthy, a cache
  miss raises :class:`CacheMissError` rather than calling out. CI sets this
  flag so notebook execution is fully offline.

This module is intentionally provider-agnostic: it knows nothing about LLMs.
The :mod:`shared.llm` module composes it with ``litellm``.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final

from .paths import repo_path

CACHE_ENV_FLAG: Final[str] = "LLM_CACHE_ONLY"
DEFAULT_CACHE_ROOT: Final[Path] = repo_path(".llm-cache")


class CacheMissError(KeyError):
    """Raised when cache-only mode is on and a key is missing."""

    def __init__(self, key: str, namespace: str) -> None:
        super().__init__(key)
        self.key = key
        self.namespace = namespace

    def __str__(self) -> str:  # pragma: no cover - trivial
        return (
            f"Cache miss for key={self.key[:12]}… in namespace={self.namespace!r} "
            f"while {CACHE_ENV_FLAG}=1. Run the notebook locally with API keys "
            f"to populate the cache, then commit the updated JSONL."
        )


def cache_only_mode() -> bool:
    """Return True when the runtime is forbidden from making live LLM calls."""
    return os.getenv(CACHE_ENV_FLAG, "0").strip().lower() in {"1", "true", "yes"}


def stable_key(payload: Mapping[str, Any]) -> str:
    """Hash a JSON-serializable mapping into a deterministic 16-char key."""
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]


class JSONLCache:
    """Thread-safe append-only JSONL cache.

    Each line is ``{"key": "<hex>", "value": <json>}``.

    Parameters
    ----------
    namespace:
        Logical name (usually the notebook slug). Becomes the filename.
    root:
        Cache root directory. Defaults to ``.llm-cache`` next to the cwd
        unless ``LLM_CACHE_DIR`` is set.
    """

    def __init__(self, namespace: str, root: Path | None = None) -> None:
        self.namespace = namespace
        env_root = os.getenv("LLM_CACHE_DIR")
        self.root = root or (Path(env_root) if env_root else DEFAULT_CACHE_ROOT)
        self.path = self.root / f"{namespace}.jsonl"
        self._lock = threading.Lock()
        self._mem: dict[str, Any] = {}
        self._loaded = False

    # -- public API ------------------------------------------------------

    def get(self, key: str) -> Any | None:
        self._ensure_loaded()
        return self._mem.get(key)

    def set(self, key: str, value: Any) -> None:
        self._ensure_loaded()
        with self._lock:
            if key in self._mem and self._mem[key] == value:
                return
            self._mem[key] = value
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"key": key, "value": value}, sort_keys=True))
                fh.write("\n")

    def lookup_or_raise(self, key: str) -> Any:
        """Return cached value, or raise :class:`CacheMissError`."""
        hit = self.get(key)
        if hit is None:
            raise CacheMissError(key, self.namespace)
        return hit

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        self._ensure_loaded()
        return key in self._mem

    def __len__(self) -> int:
        self._ensure_loaded()
        return len(self._mem)

    # -- internals -------------------------------------------------------

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        with self._lock:
            if self._loaded:  # double-checked
                return
            if self.path.exists():
                for line in self.path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    # Last write wins if duplicates exist.
                    self._mem[entry["key"]] = entry["value"]
            self._loaded = True


__all__ = [
    "CACHE_ENV_FLAG",
    "DEFAULT_CACHE_ROOT",
    "CacheMissError",
    "JSONLCache",
    "cache_only_mode",
    "stable_key",
]
