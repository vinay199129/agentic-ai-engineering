"""Shared infrastructure for the HITL leaves.

All six leaves in ``04-human-in-the-loop/`` solve the same toy scenario — a
research agent that searches the corpus, drafts an answer, and asks the human
to approve before "publishing" a citation — but each leaf wires the HITL
pattern differently (interrupt-and-resume, approval gate, edit-state,
time-travel, streaming intervention, async queue).

The runner here is a pure-Python mini-LangGraph: a state dict + nodes +
conditional edges + a checkpointer. It deliberately mirrors LangGraph's
``interrupt()`` / ``Command(resume=...)`` API so the notebooks can show real
LangGraph code in markdown while the eval falls back to this offline runner.

Design choices
--------------
* **Pure Python, no external deps.** Leaves import this module directly; CI
  doesn't need `langgraph`.
* **Deterministic.** All randomness is keyed off question id, so snapshots
  reproduce.
* **Checkpoint-first.** Every node-exit writes to the checkpointer so
  time-travel and edit-state work the same way they do in LangGraph.
* **The trace shape matches** ``03-agentic-frameworks/task.py`` so the
  per-leaf snapshot is comparable across folders.
"""

from __future__ import annotations

import copy
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any

from shared.embedders import cosine_topk, hash_embed
from shared.loaders import load_corpus, load_golden_qa

NS = "04-human-in-the-loop/shared"
DIMS = 256
SEED = 0


# ---------------------------------------------------------------------------
# Tools — same shape as the agentic-frameworks task but local to HITL so the
# two phases stay independent.
# ---------------------------------------------------------------------------

_DOCS = load_corpus()
_QA = {q.id: q for q in load_golden_qa()}
_DOC_BY_ID = {d.arxiv_id: d for d in _DOCS}
_DOC_TEXTS = [d.title + ". " + d.abstract for d in _DOCS]
_DOC_VECS = hash_embed(_DOC_TEXTS, dims=DIMS, seed=SEED)


def search(query: str, k: int = 2) -> list[dict[str, str]]:
    """Tiny dense search over the canonical corpus."""
    qv = hash_embed([query], dims=DIMS, seed=SEED)[0]
    idx, _ = cosine_topk(qv, _DOC_VECS, k=k)
    return [
        {
            "arxiv_id": _DOCS[i].arxiv_id,
            "title": _DOCS[i].title,
            "snippet": _DOCS[i].abstract[:240],
        }
        for i in idx
    ]


def draft_answer(question: str, hits: list[dict[str, str]]) -> str:
    """Deterministic, citation-rich draft built from the top hit."""
    if not hits:
        return "I don't know based on the provided context."
    top = hits[0]
    head = top["snippet"].split(".")[0]
    return f"[{top['arxiv_id']}] {head}."


def publish(answer: str, *, approved: bool) -> dict[str, Any]:
    """The "side-effectful" tool — gated by human approval in every leaf."""
    return {
        "published": approved,
        "answer": answer if approved else None,
        "ts": 0.0,  # deterministic placeholder
    }


def get_question(question_id: str) -> str:
    return _QA[question_id].question


def get_expected_sources(question_id: str) -> list[str]:
    return list(_QA[question_id].source_ids)


DEMO_IDS: tuple[str, ...] = ("q01", "q23", "q27")


# ---------------------------------------------------------------------------
# Trace + state
# ---------------------------------------------------------------------------


@dataclass
class TraceStep:
    role: str  # "node" | "interrupt" | "resume" | "final"
    name: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"role": self.role}
        if self.name is not None:
            out["name"] = self.name
        if self.payload:
            out["payload"] = self.payload
        return out


@dataclass
class AgentTrace:
    question_id: str
    pattern: str
    steps: list[TraceStep] = field(default_factory=list)
    latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "question_id": self.question_id,
            "pattern": self.pattern,
            "latency_ms": round(self.latency_ms, 3),
            "trace": [s.to_dict() for s in self.steps],
        }


# ---------------------------------------------------------------------------
# Interrupt / Command — mirrors LangGraph's HITL primitives
# ---------------------------------------------------------------------------


class Interrupt(Exception):  # noqa: N818 — mirrors LangGraph's public API name
    """Raised inside a node to pause the graph for human input."""

    def __init__(self, payload: dict[str, Any]) -> None:
        super().__init__(payload.get("reason", "interrupted"))
        self.payload = payload


@dataclass
class Command:
    """Resume value passed back into the graph."""

    resume: Any = None
    update: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Checkpointer — keyed by (thread_id, step_index). Stores deep copies so
# time-travel and edit-state are safe.
# ---------------------------------------------------------------------------


@dataclass
class Checkpoint:
    thread_id: str
    step: int
    node: str
    state: dict[str, Any]
    interrupt: dict[str, Any] | None = None


class Checkpointer:
    """In-memory checkpointer — same surface as LangGraph's MemorySaver."""

    def __init__(self) -> None:
        self._store: dict[tuple[str, int], Checkpoint] = {}

    def put(
        self,
        thread_id: str,
        step: int,
        node: str,
        state: dict[str, Any],
        interrupt: dict[str, Any] | None = None,
    ) -> Checkpoint:
        cp = Checkpoint(
            thread_id=thread_id,
            step=step,
            node=node,
            state=copy.deepcopy(state),
            interrupt=copy.deepcopy(interrupt) if interrupt else None,
        )
        self._store[(thread_id, step)] = cp
        return cp

    def get(self, thread_id: str, step: int) -> Checkpoint | None:
        cp = self._store.get((thread_id, step))
        return copy.deepcopy(cp) if cp else None

    def latest(self, thread_id: str) -> Checkpoint | None:
        keys = [k for k in self._store if k[0] == thread_id]
        if not keys:
            return None
        latest_key = max(keys, key=lambda k: k[1])
        return copy.deepcopy(self._store[latest_key])

    def history(self, thread_id: str) -> list[Checkpoint]:
        items = sorted(
            (cp for cp in self._store.values() if cp.thread_id == thread_id),
            key=lambda cp: cp.step,
        )
        return [copy.deepcopy(cp) for cp in items]

    def fork(self, thread_id: str, from_step: int, new_thread_id: str) -> Checkpoint | None:
        """Copy all checkpoints up to ``from_step`` onto a new thread id."""
        copied: Checkpoint | None = None
        for (tid, step), cp in list(self._store.items()):
            if tid == thread_id and step <= from_step:
                new_cp = Checkpoint(
                    thread_id=new_thread_id,
                    step=cp.step,
                    node=cp.node,
                    state=copy.deepcopy(cp.state),
                    interrupt=copy.deepcopy(cp.interrupt) if cp.interrupt else None,
                )
                self._store[(new_thread_id, step)] = new_cp
                if step == from_step:
                    copied = new_cp
        return copy.deepcopy(copied) if copied else None


# ---------------------------------------------------------------------------
# Graph — supervisor-style runner
# ---------------------------------------------------------------------------


Node = Callable[[dict[str, Any]], dict[str, Any]]
Route = Callable[[dict[str, Any]], str]
END = "__end__"


class Graph:
    """Tiny supervisor graph.

    * ``add_node(name, fn)``: fn receives state, returns a state delta
      (merged into state). It may raise :class:`Interrupt`.
    * ``add_edge(src, dst)``: unconditional next node.
    * ``add_conditional_edge(src, router)``: ``router(state)`` returns the
      next node name (or :data:`END`).
    * ``run(state, thread_id, checkpointer)``: walks until END or until a
      node raises :class:`Interrupt`. Returns the final state.
    * ``resume(thread_id, command, checkpointer)``: re-enters the
      interrupted node with the user-supplied value injected into state.
    """

    def __init__(self, entrypoint: str) -> None:
        self.entrypoint = entrypoint
        self.nodes: dict[str, Node] = {}
        self.edges: dict[str, str] = {}
        self.cond: dict[str, Route] = {}

    def add_node(self, name: str, fn: Node) -> None:
        self.nodes[name] = fn

    def add_edge(self, src: str, dst: str) -> None:
        self.edges[src] = dst

    def add_conditional_edge(self, src: str, router: Route) -> None:
        self.cond[src] = router

    def _next(self, current: str, state: dict[str, Any]) -> str:
        if current in self.cond:
            return self.cond[current](state)
        return self.edges.get(current, END)

    def run(
        self,
        state: dict[str, Any],
        *,
        thread_id: str,
        checkpointer: Checkpointer,
        max_steps: int = 32,
    ) -> dict[str, Any]:
        state = copy.deepcopy(state)
        state.setdefault("_steps", 0)
        state.setdefault("_trace", [])
        current = self.entrypoint
        step = state["_steps"]
        while step < max_steps:
            if current == END:
                return state
            try:
                delta = self.nodes[current](state)
            except Interrupt as exc:
                # Use step+1 so the interrupt checkpoint sits in a fresh slot
                # and does NOT clobber the previous node's post-state checkpoint
                # (which time-travel forks rely on).
                interrupt_step = step + 1
                checkpointer.put(thread_id, interrupt_step, current, state, interrupt=exc.payload)
                state["_interrupt"] = {"node": current, **exc.payload}
                state["_trace"].append(
                    TraceStep(role="interrupt", name=current, payload=exc.payload).to_dict()
                )
                state["_steps"] = interrupt_step
                return state
            state.update(delta)
            state["_trace"].append(
                TraceStep(role="node", name=current, payload={"delta_keys": list(delta)}).to_dict()
            )
            step += 1
            state["_steps"] = step
            checkpointer.put(thread_id, step, current, state)
            current = self._next(current, state)
        raise RuntimeError(f"graph exceeded max_steps={max_steps}")

    def resume(
        self,
        *,
        thread_id: str,
        command: Command,
        checkpointer: Checkpointer,
        max_steps: int = 32,
    ) -> dict[str, Any]:
        cp = checkpointer.latest(thread_id)
        if cp is None or cp.interrupt is None:
            raise RuntimeError(f"no interrupted checkpoint on thread {thread_id!r}")
        state = copy.deepcopy(cp.state)
        state.pop("_interrupt", None)
        if command.update:
            state.update(command.update)
        state["_resume_value"] = command.resume
        state["_trace"].append(
            TraceStep(
                role="resume",
                name=cp.node,
                payload={"resume": command.resume, "update": command.update},
            ).to_dict()
        )
        # Re-run the same node with the resume value available, then continue.
        try:
            delta = self.nodes[cp.node](state)
        except Interrupt as exc:
            checkpointer.put(thread_id, cp.step, cp.node, state, interrupt=exc.payload)
            state["_interrupt"] = {"node": cp.node, **exc.payload}
            return state
        state.update(delta)
        state["_trace"].append(
            TraceStep(role="node", name=cp.node, payload={"delta_keys": list(delta)}).to_dict()
        )
        state["_steps"] = cp.step + 1
        checkpointer.put(thread_id, state["_steps"], cp.node, state)
        current = self._next(cp.node, state)
        # Continue from here using a fresh run-loop.
        while state["_steps"] < max_steps:
            if current == END:
                return state
            try:
                delta = self.nodes[current](state)
            except Interrupt as exc:
                interrupt_step = state["_steps"] + 1
                checkpointer.put(thread_id, interrupt_step, current, state, interrupt=exc.payload)
                state["_interrupt"] = {"node": current, **exc.payload}
                state["_trace"].append(
                    TraceStep(role="interrupt", name=current, payload=exc.payload).to_dict()
                )
                state["_steps"] = interrupt_step
                return state
            state.update(delta)
            state["_trace"].append(
                TraceStep(role="node", name=current, payload={"delta_keys": list(delta)}).to_dict()
            )
            state["_steps"] += 1
            checkpointer.put(thread_id, state["_steps"], current, state)
            current = self._next(current, state)
        raise RuntimeError(f"graph exceeded max_steps={max_steps}")


# ---------------------------------------------------------------------------
# Canonical scenario — used by all six HITL leaves
# ---------------------------------------------------------------------------


def build_research_graph() -> Graph:
    """Build the shared `search -> draft -> approve -> publish` graph.

    The ``approve`` node always raises :class:`Interrupt` so every leaf has
    something to demonstrate. Caller decides what to do with that interrupt:
    auto-approve in tests, prompt the user in the notebook, push onto a queue
    in the async leaf, etc.
    """

    g = Graph(entrypoint="search")

    def search_node(state: dict[str, Any]) -> dict[str, Any]:
        hits = search(state["question"], k=2)
        return {"hits": hits}

    def draft_node(state: dict[str, Any]) -> dict[str, Any]:
        return {"draft": draft_answer(state["question"], state.get("hits", []))}

    def approve_node(state: dict[str, Any]) -> dict[str, Any]:
        # If the caller injected a resume value, treat that as the decision.
        if "_resume_value" in state and state["_resume_value"] is not None:
            decision = state["_resume_value"]
            return {
                "approved": bool(decision.get("approved", False)),
                "reviewer": decision.get("reviewer", "anonymous"),
                "_resume_value": None,
            }
        raise Interrupt(
            {
                "reason": "needs_human_approval",
                "draft": state.get("draft", ""),
                "options": ["approve", "deny", "edit"],
            }
        )

    def publish_node(state: dict[str, Any]) -> dict[str, Any]:
        result = publish(state.get("draft", ""), approved=bool(state.get("approved")))
        return {"published": result["published"], "final_answer": result["answer"]}

    g.add_node("search", search_node)
    g.add_node("draft", draft_node)
    g.add_node("approve", approve_node)
    g.add_node("publish", publish_node)
    g.add_edge("search", "draft")
    g.add_edge("draft", "approve")
    g.add_edge("approve", "publish")
    g.add_conditional_edge("publish", lambda _s: END)
    return g


# ---------------------------------------------------------------------------
# Eval helpers
# ---------------------------------------------------------------------------


def auto_approver(state: dict[str, Any]) -> dict[str, Any]:
    """Default reviewer used in eval: approves when the draft cites a
    document id that appears in the question's expected sources, denies
    otherwise. Matches what a careful human would do."""

    qid = state.get("question_id", "")
    expected = set(get_expected_sources(qid)) if qid in _QA else set()
    draft = state.get("draft", "")
    matched = bool(expected) and any(src in draft for src in expected)
    if not expected:
        # Unanswerable question -> reviewer must deny publishing a guess.
        return {"approved": False, "reviewer": "auto"}
    return {"approved": matched, "reviewer": "auto"}


def run_scenario(
    *,
    pattern: str,
    question_ids: tuple[str, ...] = DEMO_IDS,
    reviewer: Callable[[dict[str, Any]], dict[str, Any]] = auto_approver,
) -> dict[str, Any]:
    """Run the canonical scenario once per question and aggregate metrics."""
    per_q: list[dict[str, Any]] = []
    interrupts_fired = 0
    correct_decisions = 0
    correct_publishes = 0
    latency_total = 0.0
    for qid in question_ids:
        t0 = time.perf_counter()
        cp = Checkpointer()
        graph = build_research_graph()
        state = graph.run(
            {"question": get_question(qid), "question_id": qid},
            thread_id=qid,
            checkpointer=cp,
        )
        fired = bool(state.get("_interrupt"))
        if fired:
            interrupts_fired += 1
            decision = reviewer(state)
            state = graph.resume(
                thread_id=qid,
                command=Command(resume=decision),
                checkpointer=cp,
            )
        latency = (time.perf_counter() - t0) * 1000
        latency_total += latency

        expected = get_expected_sources(qid)
        # "Correct decision" = approved when the question is answerable AND the
        # draft cites an expected source; denied when unanswerable.
        if expected:
            expected_decision = any(src in state.get("draft", "") for src in expected)
        else:
            expected_decision = False
        if bool(state.get("approved")) == expected_decision:
            correct_decisions += 1
        # "Correct publish" = published iff approved.
        if bool(state.get("published")) == bool(state.get("approved")):
            correct_publishes += 1

        per_q.append(
            {
                "id": qid,
                "interrupt_fired": fired,
                "approved": bool(state.get("approved")),
                "published": bool(state.get("published")),
                "final_answer": state.get("final_answer"),
                "latency_ms": round(latency, 3),
                "trace": state["_trace"],
            }
        )

    n = len(question_ids)
    return {
        "pattern": pattern,
        "n_questions": n,
        "averages": {
            "interrupt_fire_rate": round(interrupts_fired / n, 4),
            "human_decision_accuracy": round(correct_decisions / n, 4),
            "publish_gating_accuracy": round(correct_publishes / n, 4),
            "avg_latency_ms": round(latency_total / n, 3),
        },
        "per_question": per_q,
    }


def stream_events(
    graph: Graph,
    initial_state: dict[str, Any],
    *,
    thread_id: str,
    checkpointer: Checkpointer,
) -> Iterator[dict[str, Any]]:
    """Step through the graph one node at a time, yielding events.

    Used by the streaming-with-intervention leaf. Yields:
    * ``{"event": "node_complete", "node": ..., "state": ...}``
    * ``{"event": "interrupt", "node": ..., "payload": ...}``
    """

    state = copy.deepcopy(initial_state)
    state.setdefault("_steps", 0)
    state.setdefault("_trace", [])
    current = graph.entrypoint
    while True:
        if current == END:
            yield {"event": "complete", "state": state}
            return
        try:
            delta = graph.nodes[current](state)
        except Interrupt as exc:
            checkpointer.put(thread_id, state["_steps"], current, state, interrupt=exc.payload)
            yield {"event": "interrupt", "node": current, "payload": exc.payload}
            return
        state.update(delta)
        state["_steps"] += 1
        checkpointer.put(thread_id, state["_steps"], current, state)
        yield {"event": "node_complete", "node": current, "delta_keys": list(delta)}
        current = graph._next(current, state)


__all__ = [
    "DEMO_IDS",
    "END",
    "NS",
    "AgentTrace",
    "Checkpoint",
    "Checkpointer",
    "Command",
    "Graph",
    "Interrupt",
    "TraceStep",
    "auto_approver",
    "build_research_graph",
    "draft_answer",
    "get_expected_sources",
    "get_question",
    "publish",
    "run_scenario",
    "search",
    "stream_events",
]
