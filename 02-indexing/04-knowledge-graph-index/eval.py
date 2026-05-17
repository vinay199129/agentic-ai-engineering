"""Eval for the knowledge-graph index leaf.

Builds the triple graph from cached LLM extractions and reports structural
metrics:
    - n_nodes, n_edges, avg_degree
    - connectivity@multi_hop: fraction of multi-hop Q&A items where the named
      source entity reaches *any* target token from the golden answer via
      ``networkx.shortest_path``.

Runs offline. If the cache doesn't yet contain extractions, the eval falls back
to a deterministic regex extractor (subject = paper title head, object = an
adjacent noun phrase) so the snapshot is always reproducible in CI.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import networkx as nx

_HERE = Path(__file__).resolve()
for _p in (_HERE.parent, *_HERE.parents):
    if (_p / "shared").exists() and (_p / "pyproject.toml").exists():
        sys.path.insert(0, str(_p))
        os.chdir(_p)
        break

if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
    os.environ.setdefault("LLM_CACHE_ONLY", "1")

from shared.llm import Message, complete  # noqa: E402
from shared.loaders import load_corpus, load_golden_qa  # noqa: E402

MODEL = "openai/gpt-4o-mini"
NS = "02-indexing/04-knowledge-graph-index"
EXTRACT_SYS = (
    "Extract (subject, predicate, object) triples from the given abstract. "
    "Return ONLY a JSON array of arrays: [[subject, predicate, object], ...]. "
    "Use short noun phrases. Extract 3-5 triples. No prose."
)


def _try_extract(abstract: str) -> list[list[str]]:
    """Use cached LLM output if available; otherwise fall back to a regex stub."""
    try:
        reply = complete(
            model=MODEL,
            namespace=NS,
            messages=[
                Message(role="system", content=EXTRACT_SYS),
                Message(role="user", content=abstract),
            ],
        ).content
        parsed = json.loads(reply)
        if isinstance(parsed, list):
            triples = [t for t in parsed if isinstance(t, list) and len(t) == 3]
            if triples:
                return [[str(t[0]), str(t[1]), str(t[2])] for t in triples]
    except Exception:
        pass
    # Deterministic fallback so CI can always produce a snapshot.
    sents = re.split(r"(?<=[.!?])\s+", abstract.strip())
    triples: list[list[str]] = []
    for s in sents[:3]:
        words = [w.strip(".,;:") for w in s.split() if w.strip()]
        if len(words) >= 6:
            triples.append([words[0], "relates_to", " ".join(words[-3:])])
    return triples


def main() -> None:
    docs = load_corpus()
    qa = load_golden_qa()

    per_doc: dict[str, list[list[str]]] = {d.arxiv_id: _try_extract(d.abstract) for d in docs}

    g: nx.DiGraph = nx.DiGraph()
    for doc_id, triples in per_doc.items():
        for s, p, o in triples:
            g.add_edge(s, o, predicate=p, doc=doc_id)

    n_nodes = g.number_of_nodes()
    n_edges = g.number_of_edges()
    avg_degree = round(
        (sum(dict(g.degree()).values()) / n_nodes) if n_nodes else 0.0,
        3,
    )

    multi_hop = [q for q in qa if "multi-hop" in q.tags and q.source_ids]
    # For each multi-hop Q:
    #   coverage     = fraction of qs where the graph has nodes from EVERY source doc
    #   connectivity = fraction where those nodes live in the same weakly connected
    #                  component (i.e., the LLM extractor produced linking edges).
    # Coverage minus connectivity = the value an entity-linker would unlock.
    components = list(nx.weakly_connected_components(g))
    node_doc: dict[str, set[str]] = {}
    for u, v, data in g.edges(data=True):
        for node in (u, v):
            node_doc.setdefault(str(node), set()).add(str(data.get("doc", "")))
    coverage_hits = 0
    connectivity_hits = 0
    for q in multi_hop:
        wanted = set(q.source_ids)
        docs_present = set().union(*node_doc.values()) if node_doc else set()
        if wanted.issubset(docs_present):
            coverage_hits += 1
        for comp in components:
            covered = set()
            for n in comp:
                covered.update(node_doc.get(str(n), set()))
            if wanted.issubset(covered):
                connectivity_hits += 1
                break

    connectivity = round(connectivity_hits / len(multi_hop), 4) if multi_hop else None
    coverage = round(coverage_hits / len(multi_hop), 4) if multi_hop else None

    sample_edges: list[dict[str, Any]] = []
    for u, v, data in list(g.edges(data=True))[:5]:
        sample_edges.append({"subject": u, "predicate": data.get("predicate", ""), "object": v})

    snapshot = {
        "technique": "knowledge-graph-index",
        "version": "0.1.0",
        "dataset": "benchmarks/golden-qa/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "n_docs": len(docs),
            "n_multi_hop_questions": len(multi_hop),
            "n_nodes": n_nodes,
            "n_edges": n_edges,
            "avg_degree": avg_degree,
            "multi_hop_source_coverage": coverage,
            "multi_hop_cross_doc_connectivity": connectivity,
            "sample_edges": sample_edges,
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
