# 0003 — LangGraph (not CrewAI) for the multi-agent deep-dive

- **Status:** accepted
- **Date:** 2025-11-15
- **Context:** Deep-dive repo #2 (`multi-agent-research-system`) needs
  to demonstrate a planner → multiple researchers → synthesiser flow
  with **mid-run human-in-the-loop interrupts** and **resumable
  execution across HTTP requests**. The Phase 5 framework tour
  ([`03-agentic-frameworks/07-framework-comparison`](../leaves/03-agentic-frameworks/07-framework-comparison/index.md))
  ran the same task across seven implementations; this ADR records
  why LangGraph wins for *this specific* deep-dive.
- **Decision:** Build the multi-agent system on **LangGraph** with
  the **`PostgresSaver` checkpointer**. Borrow the `interrupt()` /
  `Command(resume=…)` pattern explored in
  [`04-human-in-the-loop/`](../leaves/04-human-in-the-loop/index.md) (`hitl.py`).
- **Consequences:**
  - **Good** — Typed state graph makes the planner-researchers-
    synthesiser fan-out / fan-in trivial to express. The checkpointer
    lets the agent survive a Kubernetes pod restart without losing
    progress. HITL interrupts compose cleanly with the streaming HTTP
    API.
  - **Bad** — LangGraph ships breaking changes faster than we would
    like. We pin a minor version and review the changelog on every
    bump.
- **Alternatives considered:**
  - **CrewAI** — The roles abstraction would be nice for the
    planner/researcher personas, but mid-run interrupts are awkward
    and there's no first-class durable-state story comparable to
    `PostgresSaver`.
  - **MS Agent Framework** — Sequential / concurrent / group-chat
    workflows are a strong match, but the LangGraph community + tool
    integrations are deeper today and the deep-dive repo benefits
    from that ecosystem.
  - **Hand-rolled (Phase 5 `00-react-from-scratch`)** — The right
    *teaching* choice in the hub repo; the wrong production choice
    when the team isn't the same person.
