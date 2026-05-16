"""Eval for query transformation: per-strategy recall@k."""

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

from shared.embedders import cosine_topk, hash_embed  # noqa: E402
from shared.llm import Message, complete  # noqa: E402
from shared.loaders import load_corpus, load_golden_qa  # noqa: E402

MODEL = "openai/gpt-4o-mini"
NS = "01-rag/05-query-transformation"
DIMS = 256
SEED = 0
KS = (1, 3)


def _say(system: str, user: str) -> str:
    return complete(
        model=MODEL,
        namespace=NS,
        messages=[Message(role="system", content=system), Message(role="user", content=user)],
    ).content


def main() -> None:
    docs = load_corpus()
    full_qa = {q.id: q for q in load_golden_qa()}
    qa = [q for q in load_golden_qa() if q.source_ids]
    doc_texts = [d.title + ". " + d.abstract for d in docs]
    doc_ids = [d.arxiv_id for d in docs]
    doc_vecs = hash_embed(doc_texts, dims=DIMS, seed=SEED)

    def retrieve(text: str, k: int) -> list[str]:
        qv = hash_embed([text], dims=DIMS, seed=SEED)[0]
        idx, _ = cosine_topk(qv, doc_vecs, k=k)
        return [doc_ids[i] for i in idx]

    hyde_ids = {
        "q01",
        "q02",
        "q05",
        "q07",
        "q09",
        "q11",
        "q13",
        "q15",
        "q17",
        "q19",
        "q21",
    }
    mq_ids = {"q01", "q05", "q09"}
    sb_ids = {"q01", "q05", "q13"}
    dc_ids = {"q23", "q24", "q25"}

    def hit_at(retrieved: list[str], sources: list[str]) -> int:
        return int(bool(set(retrieved) & set(sources)))

    per_strategy: dict[str, dict[str, float]] = {}

    # Vanilla baseline over the same subset that has any transformation seeded — restrict to hyde_ids
    # so the comparison is apples-to-apples.
    subset = [q for q in qa if q.id in hyde_ids]
    for k in KS:
        per_strategy.setdefault("vanilla", {})[f"recall@{k}"] = round(
            sum(hit_at(retrieve(q.question, k), q.source_ids) for q in subset) / len(subset), 4
        )

    # HyDE
    for k in KS:
        hits = 0
        for q in subset:
            faked = _say(
                "Write a short, plausible-sounding passage (2-3 sentences) that "
                "ANSWERS the following research question. Do not hedge. The passage "
                "will be used purely as an embedding query — its content does not "
                "need to be true.",
                q.question,
            )
            hits += hit_at(retrieve(faked, k), q.source_ids)
        per_strategy.setdefault("hyde", {})[f"recall@{k}"] = round(hits / len(subset), 4)

    # Multi-query — union of paraphrase retrievals
    mq_subset = [q for q in qa if q.id in mq_ids]
    for k in KS:
        hits = 0
        for q in mq_subset:
            raw = _say(
                "Rewrite the user's question as 3 SEMANTICALLY EQUIVALENT alternative "
                "phrasings. One per line, no numbering, no extra prose.",
                q.question,
            )
            alts = [line.strip() for line in raw.splitlines() if line.strip()]
            union: dict[str, int] = {}
            for variant in (q.question, *alts):
                for rank, doc in enumerate(retrieve(variant, k=k)):
                    union[doc] = min(union.get(doc, 1000), rank)
            top = sorted(union, key=lambda d: union[d])[:k]
            hits += hit_at(top, q.source_ids)
        per_strategy.setdefault("multi_query", {})[f"recall@{k}"] = round(hits / len(mq_subset), 4)

    # Step-back — retrieve from the generalized question
    sb_subset = [q for q in qa if q.id in sb_ids]
    for k in KS:
        hits = 0
        for q in sb_subset:
            general = _say(
                "Given a SPECIFIC technical question, rewrite it as a MORE GENERAL "
                "question about the underlying concept. Reply with just the "
                "generalized question.",
                q.question,
            )
            hits += hit_at(retrieve(general, k), q.source_ids)
        per_strategy.setdefault("step_back", {})[f"recall@{k}"] = round(hits / len(sb_subset), 4)

    # Decomposition (multi-hop only) — union of sub-question retrievals
    dc_subset = [full_qa[i] for i in dc_ids if i in full_qa]
    for k in KS:
        hits = 0
        for q in dc_subset:
            raw = _say(
                "Decompose the user's multi-hop question into 2-3 atomic sub-questions, "
                "one per line. Each sub-question should be answerable from a SINGLE document.",
                q.question,
            )
            subs = [line.strip() for line in raw.splitlines() if line.strip()]
            union2: dict[str, int] = {}
            for s in subs:
                for rank, doc in enumerate(retrieve(s, k=k)):
                    union2[doc] = min(union2.get(doc, 1000), rank)
            top = sorted(union2, key=lambda d: union2[d])[:k]
            hits += hit_at(top, q.source_ids)
        per_strategy.setdefault("decomposition", {})[f"recall@{k}"] = round(
            hits / len(dc_subset), 4
        )

    snapshot = {
        "technique": "query-transformation",
        "version": "0.1.0",
        "dataset": "benchmarks/golden-qa/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "n_subset_hyde_and_vanilla": len(subset),
            "n_subset_multi_query": len(mq_subset),
            "n_subset_step_back": len(sb_subset),
            "n_subset_decomposition": len(dc_subset),
            "per_strategy": per_strategy,
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
