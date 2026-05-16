"""Eval for graph-rag: graph stats + community structure."""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

_HERE = Path(__file__).resolve()
for _p in (_HERE.parent, *_HERE.parents):
    if (_p / "shared").exists() and (_p / "pyproject.toml").exists():
        sys.path.insert(0, str(_p))
        os.chdir(_p)
        break
if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
    os.environ.setdefault("LLM_CACHE_ONLY", "1")

import networkx as nx  # noqa: E402

from shared.llm import Message, complete  # noqa: E402
from shared.loaders import load_corpus  # noqa: E402

MODEL = "openai/gpt-4o-mini"
NS = "01-rag/09-graph-rag"
EXTRACT_SYS = (
    "Extract the technical entities mentioned in the abstract below. "
    "Return ONLY a JSON array of short strings. No prose, no markdown. "
    "Include method names, model names, datasets, and key technical concepts. "
    "Keep it to 3-6 entities."
)


def main() -> None:
    docs = load_corpus()
    per_doc: dict[str, list[str]] = {}
    for d in docs:
        raw = complete(
            model=MODEL,
            namespace=NS,
            messages=[
                Message(role="system", content=EXTRACT_SYS),
                Message(role="user", content=d.abstract),
            ],
        ).content
        per_doc[d.arxiv_id] = json.loads(raw)

    g: nx.Graph = nx.Graph()
    for ents in per_doc.values():
        for e in ents:
            g.add_node(e)
        for i, a in enumerate(ents):
            for b in ents[i + 1 :]:
                w = g[a][b]["weight"] + 1 if g.has_edge(a, b) else 1
                g.add_edge(a, b, weight=w)
    communities = list(nx.algorithms.community.greedy_modularity_communities(g))
    sizes = sorted((len(c) for c in communities), reverse=True)
    multi_doc_communities = 0
    for c in communities:
        spans = {d for e in c for d, ents in per_doc.items() if e in ents}
        if len(spans) > 1:
            multi_doc_communities += 1

    metrics = {
        "n_docs": len(docs),
        "n_entities": g.number_of_nodes(),
        "n_edges": g.number_of_edges(),
        "n_communities": len(communities),
        "community_sizes": sizes,
        "n_multi_doc_communities": multi_doc_communities,
        "avg_entities_per_doc": round(
            sum(len(v) for v in per_doc.values()) / max(len(per_doc), 1), 2
        ),
    }
    snapshot = {
        "technique": "graph-rag",
        "version": "0.1.0",
        "dataset": "benchmarks/golden-qa/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": metrics,
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
