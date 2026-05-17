"""Shared canonical task for the agentic-frameworks tour.

Every leaf in ``03-agentic-frameworks/`` solves the same task — "research and
summarise an arxiv paper, then answer a follow-up question with citations" —
using the same three tools. The point of the tour is to compare how each
framework expresses the same agent shape; sharing the task and the tools is
what makes that comparison apples-to-apples.

Tools
-----
* :func:`search_corpus(query: str) -> list[dict]` — keyword + dense search
  over the 10-doc corpus. Returns ``[{"arxiv_id", "title", "snippet"}, ...]``.
* :func:`fetch_paper(arxiv_id: str) -> dict` — return the full record for one
  paper, or an error dict if the id is unknown.
* :func:`cite(arxiv_id: str, claim: str) -> dict` — verify ``claim`` against
  the named paper's abstract; returns ``{"supported": bool, "evidence": str}``.

The :func:`solve` function is a deterministic baseline solver written
on top of ``shared.llm.complete`` with the standard cache-aware fallback. It
is what every framework leaf falls back to when LLM_CACHE_ONLY is set, so the
eval-snapshots are reproducible in CI.

The :class:`AgentTrace` schema is the same one used by
``05-evals-and-observability/01-ragas-agent-eval``; every leaf's
``solve`` returns one so the metrics are comparable.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from shared.embedders import cosine_topk, hash_embed
from shared.llm import Message, complete
from shared.loaders import load_corpus, load_golden_qa

DIMS = 256
SEED = 0
NS = "03-agentic-frameworks/shared-task"
MODEL = "openai/gpt-4o-mini"
WORD_RE = re.compile(r"[A-Za-z0-9]+")

# ---------------------------------------------------------------------------
# Demo questions — small enough to keep eval fast, varied enough to surface
# differences. q01 is single-hop, q23 is multi-hop, q27 is unanswerable.
# ---------------------------------------------------------------------------

DEMO_IDS: tuple[str, ...] = ("q01", "q23", "q27")


# ---------------------------------------------------------------------------
# Tools — small, pure-Python, no framework deps.
# ---------------------------------------------------------------------------


_DOCS = load_corpus()
_QA = {q.id: q for q in load_golden_qa()}
_DOC_BY_ID = {d.arxiv_id: d for d in _DOCS}
_DOC_TEXTS = [d.title + ". " + d.abstract for d in _DOCS]
_DOC_VECS = hash_embed(_DOC_TEXTS, dims=DIMS, seed=SEED)


def _words(text: str) -> set[str]:
    return {w.lower() for w in WORD_RE.findall(text) if len(w) > 2}


def search_corpus(query: str, k: int = 3) -> list[dict[str, str]]:
    """Hybrid keyword+dense search; returns ranked dicts."""
    q_words = _words(query)
    qv = hash_embed([query], dims=DIMS, seed=SEED)[0]
    dense_idx, _ = cosine_topk(qv, _DOC_VECS, k=len(_DOCS))
    # RRF over dense rank + keyword-overlap rank
    keyword_scores = [
        (i, len(q_words & _words(_DOC_TEXTS[i])) / max(len(q_words), 1)) for i in range(len(_DOCS))
    ]
    keyword_scores.sort(key=lambda x: -x[1])
    keyword_order = [i for i, _ in keyword_scores]
    fused: dict[int, float] = {}
    for rank, i in enumerate(dense_idx):
        fused[int(i)] = fused.get(int(i), 0.0) + 1.0 / (60 + rank)
    for rank, i in enumerate(keyword_order):
        fused[int(i)] = fused.get(int(i), 0.0) + 1.0 / (60 + rank)
    top = sorted(fused.items(), key=lambda kv: -kv[1])[:k]
    out = []
    for i, _ in top:
        d = _DOCS[i]
        out.append(
            {
                "arxiv_id": d.arxiv_id,
                "title": d.title,
                "snippet": d.abstract[:240],
            }
        )
    return out


def fetch_paper(arxiv_id: str) -> dict[str, Any]:
    """Return the full record for ``arxiv_id`` or an error dict."""
    if arxiv_id not in _DOC_BY_ID:
        return {"error": f"document {arxiv_id!r} not found in corpus"}
    d = _DOC_BY_ID[arxiv_id]
    return {
        "arxiv_id": d.arxiv_id,
        "title": d.title,
        "abstract": d.abstract,
        "authors": d.authors,
        "year": d.year,
        "categories": d.categories,
    }


def cite(arxiv_id: str, claim: str) -> dict[str, Any]:
    """Verify ``claim`` against the named paper's abstract."""
    if arxiv_id not in _DOC_BY_ID:
        return {"supported": False, "evidence": ""}
    abstract = _DOC_BY_ID[arxiv_id].abstract
    claim_words = _words(claim)
    abs_words = _words(abstract)
    overlap = len(claim_words & abs_words) / max(len(claim_words), 1) if claim_words else 0.0
    return {
        "supported": overlap >= 0.3,
        "evidence": abstract[:240] if overlap >= 0.3 else "",
        "overlap_ratio": round(overlap, 3),
    }


TOOLS: dict[str, Callable[..., Any]] = {
    "search_corpus": search_corpus,
    "fetch_paper": fetch_paper,
    "cite": cite,
}


# ---------------------------------------------------------------------------
# Shared trace schema — same as 05-evals-and-observability/01-ragas-agent-eval.
# ---------------------------------------------------------------------------


@dataclass
class TraceStep:
    role: str  # "tool_call" | "final_answer"
    name: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)
    output_summary: str | None = None
    content: str | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"role": self.role}
        if self.role == "tool_call":
            out["name"] = self.name
            out["arguments"] = self.arguments
            out["output_summary"] = self.output_summary
        else:
            out["content"] = self.content
        return out


@dataclass
class AgentTrace:
    question_id: str
    framework: str
    steps: list[TraceStep] = field(default_factory=list)
    latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "question_id": self.question_id,
            "framework": self.framework,
            "latency_ms": round(self.latency_ms, 3),
            "trace": [s.to_dict() for s in self.steps],
        }


def get_question(question_id: str) -> str:
    return _QA[question_id].question


def get_expected_sources(question_id: str) -> list[str]:
    return list(_QA[question_id].source_ids)


# ---------------------------------------------------------------------------
# Reference solver — deterministic, offline. Every framework leaf can fall
# back to this when its real framework isn't installed / no API key set.
# ---------------------------------------------------------------------------


def solve(question: str, *, framework: str = "reference") -> AgentTrace:
    t0 = time.perf_counter()
    steps: list[TraceStep] = []

    # 1. search the corpus.
    hits = search_corpus(question, k=2)
    steps.append(
        TraceStep(
            role="tool_call",
            name="search_corpus",
            arguments={"query": question},
            output_summary=f"Top hits: {[h['arxiv_id'] for h in hits]}",
        )
    )

    if not hits:
        steps.append(
            TraceStep(
                role="final_answer",
                content="I don't know based on the provided context.",
            )
        )
        return AgentTrace(
            question_id="?",
            framework=framework,
            steps=steps,
            latency_ms=(time.perf_counter() - t0) * 1000,
        )

    # 2. fetch the top paper for grounded summary.
    top = hits[0]
    paper = fetch_paper(top["arxiv_id"])
    steps.append(
        TraceStep(
            role="tool_call",
            name="fetch_paper",
            arguments={"arxiv_id": top["arxiv_id"]},
            output_summary=f"Title: {paper.get('title', '?')}",
        )
    )

    # 3. ask the model for a grounded answer (cached call; fallback below).
    answer = _synthesize(question, [paper] + [fetch_paper(h["arxiv_id"]) for h in hits[1:]])

    # 4. cite the answer's main claim.
    citation = cite(top["arxiv_id"], answer)
    steps.append(
        TraceStep(
            role="tool_call",
            name="cite",
            arguments={"arxiv_id": top["arxiv_id"], "claim": answer[:120]},
            output_summary=f"supported={citation['supported']} overlap={citation['overlap_ratio']}",
        )
    )

    steps.append(TraceStep(role="final_answer", content=answer))
    return AgentTrace(
        question_id="?",
        framework=framework,
        steps=steps,
        latency_ms=(time.perf_counter() - t0) * 1000,
    )


_SYNTHESIZE_SYS = (
    "You are a research summariser. Using ONLY the provided papers, write a "
    "2-sentence answer to the question. Cite each paper by its [arxiv_id]. "
    "If the answer is not in the papers, say 'I don't know based on the "
    "provided context.'"
)


def _synthesize(question: str, papers: list[dict[str, Any]]) -> str:
    block = "\n\n".join(
        f"[{p.get('arxiv_id', '?')}] {p.get('title', '')}. {p.get('abstract', '')[:400]}"
        for p in papers
        if "arxiv_id" in p
    )
    try:
        return complete(
            model=MODEL,
            namespace=NS,
            messages=[
                Message(role="system", content=_SYNTHESIZE_SYS),
                Message(
                    role="user",
                    content=f"Question: {question}\n\nPapers:\n{block}\n\nAnswer:",
                ),
            ],
        ).content
    except Exception:
        # Deterministic fallback: stitch a citation-only answer from the top paper.
        if not papers or "arxiv_id" not in papers[0]:
            return "I don't know based on the provided context."
        p = papers[0]
        head = p.get("abstract", "").split(".")[0]
        return f"[{p['arxiv_id']}] {head}."


# ---------------------------------------------------------------------------
# Eval helpers — shared by every framework leaf so snapshots are comparable.
# ---------------------------------------------------------------------------


def run_evaluation(
    solver: Callable[[str], AgentTrace],
    framework: str,
    question_ids: tuple[str, ...] = DEMO_IDS,
) -> dict[str, Any]:
    per_q: list[dict[str, Any]] = []
    n_steps_total = 0
    grounded_hits = 0
    tool_hits: float = 0.0
    latency_total = 0.0
    for qid in question_ids:
        q = get_question(qid)
        trace = solver(q)
        trace.question_id = qid
        trace.framework = framework
        n_steps_total += len(trace.steps)
        latency_total += trace.latency_ms
        tool_calls = [s for s in trace.steps if s.role == "tool_call"]
        expected_tools = {"search_corpus", "fetch_paper", "cite"}
        # tool_call_accuracy here = jaccard over expected tools
        called = {s.name for s in tool_calls}
        tool_hits += len(called & expected_tools) / max(len(expected_tools), 1)
        # final answer grounded? overlap with at least one expected source title
        final = next(
            (s.content for s in reversed(trace.steps) if s.role == "final_answer"),
            "",
        )
        expected_src = get_expected_sources(qid)
        if not expected_src:
            grounded = "i don't know" in (final or "").lower()
        else:
            grounded = any(src in (final or "") for src in expected_src)
        grounded_hits += 1 if grounded else 0
        per_q.append(
            {
                "id": qid,
                "n_steps": len(trace.steps),
                "latency_ms": round(trace.latency_ms, 3),
                "tool_accuracy": round(
                    len(called & expected_tools) / max(len(expected_tools), 1), 4
                ),
                "grounded": grounded,
                "trace": trace.to_dict()["trace"],
            }
        )

    n = len(question_ids)
    return {
        "framework": framework,
        "n_questions": n,
        "averages": {
            "tool_call_accuracy": round(tool_hits / n, 4),
            "final_answer_grounded": round(grounded_hits / n, 4),
            "avg_n_steps": round(n_steps_total / n, 3),
            "avg_latency_ms": round(latency_total / n, 3),
        },
        "per_question": per_q,
    }


__all__ = [
    "DEMO_IDS",
    "MODEL",
    "TOOLS",
    "AgentTrace",
    "TraceStep",
    "cite",
    "fetch_paper",
    "get_expected_sources",
    "get_question",
    "run_evaluation",
    "search_corpus",
    "solve",
]
