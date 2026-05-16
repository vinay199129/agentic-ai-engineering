"""Download a slice of arxiv-cs.CL for the canonical hub corpus.

Run locally (CI never runs this — it hits the network):

.. code-block:: bash

    uv sync --group corpus
    uv run python benchmarks/corpus/download.py --max 500

Outputs ``benchmarks/corpus/metadata.jsonl`` and (optionally) downloads PDFs
into ``benchmarks/corpus/raw/`` (git-ignored).

The committed ``metadata.jsonl`` in this folder is a small **synthetic** seed
corpus so notebooks, tests, and CI run offline. Real users overwrite it by
running this script.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
METADATA = HERE / "metadata.jsonl"
RAW_DIR = HERE / "raw"


def fetch_arxiv(max_results: int, category: str, since_year: int) -> list[dict[str, Any]]:
    """Query arxiv via the ``arxiv`` package; return JSON-friendly metadata dicts."""
    try:
        import arxiv
    except ImportError as exc:  # pragma: no cover - depends on optional dep
        raise SystemExit(
            "The `arxiv` package is required. Install with `uv sync --group corpus`."
        ) from exc

    search = arxiv.Search(
        query=f"cat:{category}",
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )
    client = arxiv.Client(page_size=100, delay_seconds=3.0, num_retries=3)
    out: list[dict[str, Any]] = []
    for result in client.results(search):
        if result.published.year < since_year:
            continue
        out.append(
            {
                "arxiv_id": result.entry_id.rsplit("/", 1)[-1],
                "title": result.title.strip().replace("\n", " "),
                "abstract": result.summary.strip().replace("\n", " "),
                "authors": [a.name for a in result.authors],
                "year": result.published.year,
                "categories": result.categories,
                "url": result.entry_id,
            }
        )
    return out


def write_metadata(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False))
            fh.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max", type=int, default=500, help="Max papers (default: 500)")
    parser.add_argument("--category", default="cs.CL", help="arxiv category (default: cs.CL)")
    parser.add_argument("--since-year", type=int, default=2024, help="Earliest year")
    parser.add_argument("--out", type=Path, default=METADATA, help="Output JSONL path")
    args = parser.parse_args(argv)

    rows = fetch_arxiv(max_results=args.max, category=args.category, since_year=args.since_year)
    write_metadata(rows, args.out)
    print(f"Wrote {len(rows)} papers to {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    sys.exit(main())
