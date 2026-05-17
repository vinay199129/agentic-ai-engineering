"""Eval for the Langfuse-style tracing leaf.

Runs a tiny RAG trace through the in-memory recorder and asserts structural
invariants — number of spans, parent chain correctness, score coverage, and
duration distribution.
"""

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

sys.path.insert(0, str(_HERE.parent))

from recorder import InMemoryTracer  # noqa: E402

from shared.embedders import cosine_topk, hash_embed  # noqa: E402
from shared.loaders import load_corpus, load_golden_qa  # noqa: E402

DIMS = 256
SEED = 0
K = 3
DEMO_IDS = ["q01", "q05", "q23"]


def main() -> None:
    docs = load_corpus()
    qa = {q.id: q for q in load_golden_qa()}
    doc_texts = [d.title + ". " + d.abstract for d in docs]
    doc_ids = [d.arxiv_id for d in docs]
    doc_vecs = hash_embed(doc_texts, dims=DIMS, seed=SEED)

    tracer = InMemoryTracer()
    for qid in DEMO_IDS:
        item = qa[qid]
        with tracer.trace("rag_request", question_id=item.id) as t:
            with tracer.span("retrieve") as r:
                qv = hash_embed([item.question], dims=DIMS, seed=SEED)[0]
                idx, _scores = cosine_topk(qv, doc_vecs, k=K)
                retrieved_ids = [doc_ids[i] for i in idx]
                r.update(input=item.question, output=retrieved_ids)
                hit = bool(set(retrieved_ids) & set(item.source_ids))
                r.score("recall_at_k_hit", hit)

            with tracer.span("generate") as g:
                # No LLM call here — we just record the structure.
                fake_answer = "[" + retrieved_ids[0] + "] " + doc_texts[idx[0]][:80] + "..."
                g.update(input=retrieved_ids, output=fake_answer)
                g.score("answer_length_chars", len(fake_answer))

            t.update(output=fake_answer)
            t.score("trace_ok", True)

    # --- structural invariants ----------------------------------------
    n_traces = len(tracer.traces)
    n_spans = len(tracer.spans)
    avg_duration_ms = round(sum(s.duration_ms for s in tracer.spans) / max(n_spans, 1), 4)
    parent_ok = all(
        (s.parent_id is None and s.name == "rag_request")
        or any(p.span_id == s.parent_id for p in tracer.spans)
        for s in tracer.spans
    )
    scores_total = sum(len(s.scores) for s in tracer.spans)
    spans_with_scores = sum(1 for s in tracer.spans if s.scores)

    snapshot = {
        "technique": "langfuse-tracing",
        "version": "0.1.0",
        "dataset": "benchmarks/golden-qa/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "n_traces": n_traces,
            "n_spans": n_spans,
            "spans_with_scores": spans_with_scores,
            "scores_total": scores_total,
            "avg_duration_ms": avg_duration_ms,
            "parent_chain_valid": parent_ok,
            "demo_question_ids": DEMO_IDS,
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
