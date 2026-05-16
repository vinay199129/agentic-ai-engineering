"""Eval for Agentic RAG: tool routing accuracy + answer presence."""

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
from shared.llm import Message, ToolSpec, complete  # noqa: E402
from shared.loaders import load_corpus, load_golden_qa  # noqa: E402

MODEL = "openai/gpt-4o-mini"
NS = "01-rag/08-agentic-rag"

TOOLS = [
    ToolSpec(
        name="search_papers",
        description="Semantic search over the arxiv-cs.CL synthetic corpus. Returns top doc ids.",
        parameters={
            "type": "object",
            "properties": {"query": {"type": "string"}, "k": {"type": "integer", "default": 3}},
            "required": ["query"],
        },
    ),
    ToolSpec(
        name="lookup_doc",
        description="Return the full abstract for a single doc id (e.g. 'synth-001').",
        parameters={
            "type": "object",
            "properties": {"doc_id": {"type": "string"}},
            "required": ["doc_id"],
        },
    ),
    ToolSpec(
        name="answer_directly",
        description="Use when the question needs no retrieval (greeting, definition of a generic term).",
        parameters={
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"],
        },
    ),
]

AGENT_SYS = (
    "You are a research assistant with three tools: search_papers, lookup_doc, answer_directly. "
    "First pick the SINGLE best tool for the user's question, then after seeing its result give "
    "a concise final answer grounded in the tool output. Never invent citations."
)

EXAMPLES = [
    {"q": None, "qid": "q01", "expected_route": "search_papers"},
    {"q": "Give me the abstract of synth-005.", "qid": None, "expected_route": "lookup_doc"},
    {
        "q": "What does the abbreviation RAG stand for in NLP?",
        "qid": None,
        "expected_route": "answer_directly",
    },
]


def main() -> None:
    docs = load_corpus()
    qa = {q.id: q for q in load_golden_qa()}
    doc_by_id = {d.arxiv_id: d for d in docs}
    doc_texts = [d.title + ". " + d.abstract for d in docs]
    doc_ids = [d.arxiv_id for d in docs]
    doc_vecs = hash_embed(doc_texts, dims=256, seed=0)

    def t_search(query: str, k: int = 3) -> list[dict[str, str]]:
        qv = hash_embed([query], dims=256, seed=0)[0]
        idx, _ = cosine_topk(qv, doc_vecs, k=k)
        return [{"doc_id": doc_ids[i], "snippet": doc_texts[i][:120]} for i in idx]

    def t_lookup(doc_id: str) -> dict[str, str]:
        d = doc_by_id[doc_id]
        return {"doc_id": doc_id, "title": d.title, "abstract": d.abstract}

    def t_direct(answer: str) -> str:
        return answer

    dispatch = {"search_papers": t_search, "lookup_doc": t_lookup, "answer_directly": t_direct}

    routes_correct = 0
    answers_non_empty = 0
    per_route: dict[str, int] = {}
    for ex in EXAMPLES:
        user_q = qa[ex["qid"]].question if ex["qid"] else ex["q"]
        msgs = [Message(role="system", content=AGENT_SYS), Message(role="user", content=user_q)]
        first = complete(model=MODEL, namespace=NS, messages=msgs, tools=TOOLS)
        if not first.tool_calls:
            continue
        call = first.tool_calls[0]
        per_route[call.name] = per_route.get(call.name, 0) + 1
        if call.name == ex["expected_route"]:
            routes_correct += 1
        args = json.loads(call.arguments)
        result = dispatch[call.name](**args)
        payload = result if isinstance(result, str) else json.dumps(result)
        msgs_after = [
            *msgs,
            Message(role="assistant", content=""),
            Message(role="tool", name=call.name, content=payload),
        ]
        final = complete(model=MODEL, namespace=NS, messages=msgs_after)
        if final.content.strip():
            answers_non_empty += 1

    metrics = {
        "n_examples": len(EXAMPLES),
        "route_accuracy": round(routes_correct / len(EXAMPLES), 4),
        "answer_non_empty_rate": round(answers_non_empty / len(EXAMPLES), 4),
        "route_distribution": per_route,
    }
    snapshot = {
        "technique": "agentic-rag",
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
