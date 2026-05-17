# agentic-ai-engineering

> A hands-on portfolio of agentic AI engineering — every major RAG technique, every major agent framework, human-in-the-loop patterns, indexing internals, evals, MCP, and deployment.

This site is generated from the repo's docs. The repo itself is the primary artifact — every topic folder is runnable.

## Two deep-dive repos

- **production-rag-pipeline** — production hybrid RAG with self-hosted Langfuse, RAGAS regression in CI, Streamlit chat, Fly.io deploy
- **multi-agent-research-system** — LangGraph supervisor + 5 specialists, HITL approval gates, MCP-only tools, Postgres checkpointer with time-travel

## Where to start

- [**Dashboard**](dashboard.md) — what shipped at a glance (8 phases, 52 leaves, headline metrics)
- [**Leaderboard**](leaderboard.md) — every leaf with its committed eval numbers
- [Learning path](learning-path.md) — recommended traversal order
- [Skills matrix](skills-matrix.md) — what each folder demonstrates
- [Architecture](architecture.md) — system-level mermaid diagrams
- [Built from scratch](from-scratch.md) — ~4 200 lines of pedagogical re-implementations (MCP, mini-LangGraph, HNSW, IVF-PQ, RAGAS metrics, judge, regression gate)
- [Real-world case studies](case-studies.md) — every leaf mapped to a production problem (customer support, internal API agents, DevOps runbooks, healthcare HITL, multi-doc research)
- [Run in browser](browser-execution.md) — ~38 of 55 notebooks run with zero install via JupyterLite (Pyodide)
- [Deep-dives](deep-dives/index.md) — long-form write-ups for the five highest-signal techniques
- [Architecture decisions](architecture-decisions/README.md) — why things are the way they are
- [Launch checklist](launch-checklist.md) — soft-launch runbook + draft posts
