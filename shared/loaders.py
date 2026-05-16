"""Tiny loaders for the canonical corpus and golden Q&A.

All loaders are read-only and pure-function — they don't hit the network. The
arxiv fetcher lives in :mod:`benchmarks.corpus.download` and writes the
``metadata.jsonl`` consumed here.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from .paths import repo_path

DEFAULT_CORPUS_METADATA = repo_path("benchmarks", "corpus", "metadata.jsonl")
DEFAULT_GOLDEN_QA = repo_path("benchmarks", "golden-qa", "v1.jsonl")


class ArxivDoc(BaseModel):
    """One arxiv paper. ``text`` is the abstract; full-text PDFs are optional."""

    arxiv_id: str
    title: str
    abstract: str
    authors: list[str] = Field(default_factory=list)
    year: int
    categories: list[str] = Field(default_factory=list)
    url: str | None = None

    @property
    def text(self) -> str:
        return self.abstract


class QAItem(BaseModel):
    """A golden Q&A pair with reference answer and source documents."""

    id: str
    question: str
    answer: str
    source_ids: list[str]
    tags: list[str] = Field(default_factory=list)


def _iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            yield json.loads(line)


def load_corpus(path: Path | None = None) -> list[ArxivDoc]:
    """Load the canonical arxiv metadata JSONL into :class:`ArxivDoc` objects."""
    target = path or DEFAULT_CORPUS_METADATA
    if not target.exists():
        raise FileNotFoundError(
            f"Corpus metadata not found at {target}. "
            "Run `uv run python benchmarks/corpus/download.py` to populate it, "
            "or use the committed sample at benchmarks/corpus/metadata.jsonl."
        )
    return [ArxivDoc.model_validate(row) for row in _iter_jsonl(target)]


def load_golden_qa(path: Path | None = None) -> list[QAItem]:
    """Load the hand-curated Q&A set."""
    target = path or DEFAULT_GOLDEN_QA
    if not target.exists():
        raise FileNotFoundError(f"Golden Q&A not found at {target}.")
    return [QAItem.model_validate(row) for row in _iter_jsonl(target)]


def load_pdf_text(path: Path) -> str:
    """Extract concatenated text from a PDF. ``pypdf`` is a soft dependency."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - depends on optional dep
        raise ImportError(
            "pypdf is required for PDF loading. Install it via `uv sync --group corpus`."
        ) from exc
    reader = PdfReader(str(path))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages)


__all__ = [
    "DEFAULT_CORPUS_METADATA",
    "DEFAULT_GOLDEN_QA",
    "ArxivDoc",
    "QAItem",
    "load_corpus",
    "load_golden_qa",
    "load_pdf_text",
]
