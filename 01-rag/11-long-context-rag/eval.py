"""Eval for long-context-rag: recall@{1,3,5} bare vs contextualized chunks."""

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
NS = "01-rag/11-long-context-rag"
SUBSET = ["synth-001", "synth-002", "synth-003", "synth-004", "synth-005"]
KS = (1, 3, 5)

CTX_SYS = (
    "You are summarizing the position of a chunk inside its full document. Given the document "
    "and a single chunk, produce a SHORT (<=20 words) context prefix that situates the chunk. "
    "Do not restate the chunk. Output ONLY the prefix, no quoting, no extra prose."
)


def split_doc(text: str) -> list[str]:
    sentences = text.replace("?", "?.").replace("!", "!.").split(". ")
    mid = max(1, len(sentences) // 2)
    head = ". ".join(sentences[:mid]).strip()
    tail = ". ".join(sentences[mid:]).strip()
    if head and not head.endswith("."):
        head += "."
    if tail and not tail.endswith("."):
        tail += "."
    return [head, tail]


def main() -> None:
    docs = [d for d in load_corpus() if d.arxiv_id in SUBSET]
    qa = [q for q in load_golden_qa() if any(s in SUBSET for s in q.source_ids)]

    chunks: list[tuple[str, int, str]] = []
    for d in docs:
        for i, c in enumerate(split_doc(d.abstract)):
            chunks.append((d.arxiv_id, i, c))

    def prefix_for(doc, chunk: str) -> str:  # type: ignore[no-untyped-def]
        user = (
            f"<document>\n{doc.title}. {doc.abstract}\n</document>\n\n"
            f"<chunk>\n{chunk}\n</chunk>\n\nContext prefix:"
        )
        return complete(
            model=MODEL,
            namespace=NS,
            messages=[
                Message(role="system", content=CTX_SYS),
                Message(role="user", content=user),
            ],
        ).content.strip()

    doc_by_id = {d.arxiv_id: d for d in docs}
    augmented = [(did, ci, c, prefix_for(doc_by_id[did], c)) for did, ci, c in chunks]
    bare_vecs = hash_embed([c for _, _, c, _ in augmented], dims=256, seed=0)
    ctx_vecs = hash_embed([f"{p} {c}" for _, _, c, p in augmented], dims=256, seed=0)

    def recall(matrix, k: int) -> float:  # type: ignore[no-untyped-def]
        hits = 0
        for q in qa:
            qv = hash_embed([q.question], dims=256, seed=0)[0]
            idx, _ = cosine_topk(qv, matrix, k=k)
            got = {augmented[i][0] for i in idx}
            if got & set(q.source_ids):
                hits += 1
        return round(hits / len(qa), 4)

    per_k = {
        f"recall@{k}": {"bare": recall(bare_vecs, k), "contextual": recall(ctx_vecs, k)} for k in KS
    }
    snapshot = {
        "technique": "long-context-rag",
        "version": "0.1.0",
        "dataset": "benchmarks/golden-qa/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "n_subset_docs": len(docs),
            "n_chunks": len(chunks),
            "n_questions": len(qa),
            **per_k,
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
