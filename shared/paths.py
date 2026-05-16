"""Helpers to locate the repository root from anywhere inside it.

Notebooks execute from their leaf folder (e.g. ``01-rag/00-naive-rag/``), so any
cwd-relative path resolves wrong. Functions here walk up from the caller's cwd
until they find a marker that uniquely identifies the repo root (the
``pyproject.toml`` next to a ``shared/`` directory), then return that path.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def repo_root(start: Path | None = None) -> Path:
    """Return the absolute path to the repository root.

    Walks upward from ``start`` (default: cwd) looking for a directory that
    contains both ``pyproject.toml`` and a ``shared/`` folder. Falls back to
    the cwd if no marker is found, so this never raises.
    """
    env_override = os.getenv("AGENTIC_AI_REPO_ROOT")
    if env_override:
        return Path(env_override).resolve()
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "pyproject.toml").exists() and (candidate / "shared").exists():
            return candidate
    return here


def repo_path(*parts: str) -> Path:
    """Resolve a path relative to the repo root."""
    return repo_root().joinpath(*parts)


__all__ = ["repo_path", "repo_root"]
