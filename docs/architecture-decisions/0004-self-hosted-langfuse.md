# 0004 — Self-hosted Langfuse as the observability stack

- **Status:** accepted
- **Date:** 2025-11-22
- **Context:** Phase 4 demands structured tracing for every LLM call,
  tool call, and HITL interrupt across the hub and both deep-dive
  repos, with the ability to inspect failed runs offline and to drive
  the regression suite from real production traces. SaaS observability
  vendors (LangSmith, Helicone, Phoenix Cloud) all offer this. So
  does self-hosting.
- **Decision:** Use **self-hosted Langfuse** running via the Phase 8
  [`docker-compose-stack`](../leaves/07-deployment-patterns/02-docker-compose-stack/index.md)
  leaf. Trace decoration lives in
  [`05-evals-and-observability/02-langfuse-tracing/`](../leaves/05-evals-and-observability/02-langfuse-tracing/index.md) (`recorder.py`).
  Storage backend: Postgres (same instance as `pgvector`).
- **Consequences:**
  - **Good** — Traces never leave the host. The hub stays
    fully reproducible inside `docker compose up` with no external
    accounts required. The Langfuse data model (sessions → traces →
    spans → generations) is rich enough to power both UI inspection
    and offline analysis through SQL.
  - **Good** — Self-hosting forces the team to think about retention
    and cost early. Saves a surprise migration off SaaS later.
  - **Bad** — One more service to operate. Mitigated by the fact
    that Postgres is already in the stack.
  - **Bad** — The Langfuse UI lags the hosted version by a release or
    two. Acceptable for a portfolio; would re-evaluate for a customer-
    facing product.
- **Alternatives considered:**
  - **LangSmith (hosted)** — Best DX; cost grows aggressively past
    a few million spans/month and creates a hard dependency on a
    third-party for any reproducibility story.
  - **Helicone** — Strong on cost analytics; weaker on the
    trace-tree model we need for HITL flows.
  - **Phoenix (Arize) self-hosted** — Genuinely excellent; close
    second choice. Langfuse won because its prompt-management story
    integrates with the MCP `prompts/*` pattern we want to lean on.
