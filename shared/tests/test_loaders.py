"""Tests for shared.loaders."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shared.loaders import ArxivDoc, QAItem, load_corpus, load_golden_qa


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def test_load_corpus_parses_arxiv_docs(tmp_path: Path) -> None:
    path = tmp_path / "metadata.jsonl"
    _write_jsonl(
        path,
        [
            {
                "arxiv_id": "2401.00001",
                "title": "Test",
                "abstract": "An abstract.",
                "authors": ["A", "B"],
                "year": 2024,
                "categories": ["cs.CL"],
            }
        ],
    )
    docs = load_corpus(path)
    assert len(docs) == 1
    assert isinstance(docs[0], ArxivDoc)
    assert docs[0].text == "An abstract."


def test_load_corpus_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_corpus(tmp_path / "nope.jsonl")


def test_load_golden_qa_parses_items(tmp_path: Path) -> None:
    path = tmp_path / "qa.jsonl"
    _write_jsonl(
        path,
        [
            {
                "id": "q1",
                "question": "What is X?",
                "answer": "Y.",
                "source_ids": ["2401.00001"],
                "tags": ["definition"],
            }
        ],
    )
    items = load_golden_qa(path)
    assert items[0] == QAItem(
        id="q1",
        question="What is X?",
        answer="Y.",
        source_ids=["2401.00001"],
        tags=["definition"],
    )


def test_load_corpus_skips_comments_and_blanks(tmp_path: Path) -> None:
    path = tmp_path / "metadata.jsonl"
    path.write_text(
        "\n".join(
            [
                "# header comment",
                "",
                json.dumps(
                    {
                        "arxiv_id": "2401.00002",
                        "title": "T",
                        "abstract": "A",
                        "year": 2024,
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )
    docs = load_corpus(path)
    assert len(docs) == 1
