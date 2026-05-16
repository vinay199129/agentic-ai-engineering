"""Eval for reranking: recall@1 before/after each reranker."""

from __future__ import annotations

import json
import os
import re
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

from shared.embedders import cosine_topk, hash_embed  # noqa: E402
from shared.llm import Message, complete  # noqa: E402
from shared.loaders import load_corpus, load_golden_qa  # noqa: E402

MODEL = "openai/gpt-4o-mini"
NS = "01-rag/04-reranking"
DIMS = 256
SEED = 0
K_FIRST = 5

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def tok(t: str) -> set[str]:
    return {w.lower() for w in TOKEN_RE.findall(t) if len(w) > 3}


def crossenc_score(q: str, d: str) -> float:
    qt, dt = tok(q), tok(d)
    if not qt or not dt:
        return 0.0
    return len(qt & dt) / (len(dt) ** 0.5)


def main() -> None:
    docs = load_corpus()
    qa = [q for q in load_golden_qa() if q.source_ids]
    doc_texts = [d.title + ". " + d.abstract for d in docs]
    doc_ids = [d.arxiv_id for d in docs]
    doc_vecs = hash_embed(doc_texts, dims=DIMS, seed=SEED)

    def first_stage(q: str) -> list[tuple[str, str]]:
        qv = hash_embed([q], dims=DIMS, seed=SEED)[0]
        idx, _ = cosine_topk(qv, doc_vecs, k=K_FIRST)
        return [(doc_ids[i], doc_texts[i]) for i in idx]

    def rerank_crossenc(q: str, cands: list[tuple[str, str]]) -> list[tuple[str, str]]:
        return sorted(cands, key=lambda c: -crossenc_score(q, c[1]))

    def rerank_llm(q: str, cands: list[tuple[str, str]]) -> list[tuple[str, str]]:
        ctx = "\n\n".join(f"[{doc_id}] {text[:200]}..." for doc_id, text in cands)
        sys_p = (
            "You are a precise relevance ranker. Given a question and a list of candidate "
            "passages, return ONLY the bracketed id of the MOST relevant passage."
        )
        user_p = f"Question: {q}\n\nCandidates:\n{ctx}\n\nMost relevant id:"
        pick = complete(
            model=MODEL,
            namespace=NS,
            messages=[Message(role="system", content=sys_p), Message(role="user", content=user_p)],
        ).content.strip()
        pick_id = pick.strip("[]").split()[0] if pick else cands[0][0]
        return [c for c in cands if c[0] == pick_id] + [c for c in cands if c[0] != pick_id]

    counts = {"no_rerank": 0, "crossenc": 0, "llm": 0}
    for item in qa:
        cands = first_stage(item.question)
        if cands[0][0] in item.source_ids:
            counts["no_rerank"] += 1
        if rerank_crossenc(item.question, cands)[0][0] in item.source_ids:
            counts["crossenc"] += 1
        if rerank_llm(item.question, cands)[0][0] in item.source_ids:
            counts["llm"] += 1

    metrics = {
        "n_questions": len(qa),
        "k_first_stage": K_FIRST,
        "recall@1": {k: round(v / len(qa), 4) for k, v in counts.items()},
    }
    snapshot = {
        "technique": "reranking",
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
