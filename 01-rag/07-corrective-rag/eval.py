"""Eval for CRAG: per-verdict routing accuracy on the 5-Q subset."""

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
from shared.prompts import RAG_SYSTEM, rag_user_prompt  # noqa: E402

MODEL = "openai/gpt-4o-mini"
NS = "01-rag/07-corrective-rag"
SUBSET = ["q01", "q11", "q07", "q27", "q28"]
EXPECTED_VERDICT = {
    "q01": "confident",
    "q11": "confident",
    "q07": "ambiguous",
    "q27": "insufficient",
    "q28": "insufficient",
}
WEB = {
    "q07": "Wikipedia (Mixture-of-Experts): MoE layers route each token to a small subset of expert sub-networks.",
    "q27": "(no external source disagrees with the in-corpus refusal; topic is out of scope)",
    "q28": "Public FAQ: this benchmark does not measure latency on edge devices.",
}


def main() -> None:
    docs = load_corpus()
    qa = {q.id: q for q in load_golden_qa()}
    doc_texts = [d.title + ". " + d.abstract for d in docs]
    doc_ids = [d.arxiv_id for d in docs]
    doc_vecs = hash_embed(doc_texts, dims=256, seed=0)

    def retrieve(q: str, k: int = 3) -> list[tuple[str, str]]:
        qv = hash_embed([q], dims=256, seed=0)[0]
        idx, _ = cosine_topk(qv, doc_vecs, k=k)
        return [(doc_ids[i], doc_texts[i]) for i in idx]

    grader_sys = (
        "You judge whether retrieved documents are sufficient to answer a question. "
        "Reply with EXACTLY one token: 'confident', 'ambiguous', or 'insufficient'."
    )

    def grade(q: str, passages: list[tuple[str, str]]) -> str:
        ctx = "\n\n".join(f"[{d}] {t}" for d, t in passages)
        out = (
            complete(
                model=MODEL,
                namespace=NS,
                messages=[
                    Message(role="system", content=grader_sys),
                    Message(role="user", content=f"Question: {q}\n\nRetrieved:\n{ctx}\n\nVerdict:"),
                ],
            )
            .content.strip()
            .lower()
        )
        return out.split()[0] if out else "insufficient"

    def answer(q: str, contexts: list[tuple[str, str]]) -> str:
        return complete(
            model=MODEL,
            namespace=NS,
            messages=[
                Message(role="system", content=RAG_SYSTEM),
                Message(role="user", content=rag_user_prompt(q, contexts)),
            ],
        ).content

    verdict_correct = 0
    answers_per_verdict: dict[str, int] = {"confident": 0, "ambiguous": 0, "insufficient": 0}
    for qid in SUBSET:
        item = qa[qid]
        passages = retrieve(item.question, k=3)
        v = grade(item.question, passages)
        if v == EXPECTED_VERDICT[qid]:
            verdict_correct += 1
        if v == "confident":
            ctx = passages
        elif v == "ambiguous":
            ctx = [*passages, ("web", WEB.get(qid, ""))]
        else:
            ctx = [("web", WEB.get(qid, ""))]
        _ = answer(item.question, ctx)
        answers_per_verdict[v] = answers_per_verdict.get(v, 0) + 1

    metrics = {
        "n_subset": len(SUBSET),
        "verdict_accuracy": round(verdict_correct / len(SUBSET), 4),
        "route_distribution": answers_per_verdict,
    }
    snapshot = {
        "technique": "corrective-rag",
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
