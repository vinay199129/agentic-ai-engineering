# 0001 — Use `uv` as the package manager

- **Status:** accepted
- **Date:** 2025-11-01
- **Context:** The hub spans a dozen experimental sub-folders, each with
  partially-overlapping but distinct runtime dependencies (RAG stack,
  agentic-frameworks tour, evals, MCP). We need a tool that handles
  multiple dependency groups, locks deterministically, and is fast
  enough to be invoked on every `git push` from CI without anyone
  noticing.
- **Decision:** Use [`uv`](https://docs.astral.sh/uv/) as the canonical
  package manager. Manage runtime + phase-specific dependencies through
  the `pyproject.toml` `[dependency-groups]` table (`rag`, `indexing`,
  `frameworks`, `evals`, `hitl`, `mcp`, `deployment`). Commit
  `uv.lock`.
- **Consequences:**
  - **Good** — Install times in CI dropped from ~80 s (Poetry) to
    ~6 s. Dependency groups let leaves install only what they need.
    `uv run` gives every contributor a predictable virtualenv with one
    command and no shell-activation footgun.
  - **Bad** — `uv` is younger than Poetry; some plugins (e.g. private
    indexes with non-PEP-503 auth) still have rough edges. We accept
    that risk because nothing here pulls from private indexes.
- **Alternatives considered:**
  - **Poetry** — Mature, but its resolver is the slow path in CI and
    its lock format has historically churned across major versions.
  - **pip + `requirements*.txt`** — Conceptually the simplest, but
    leaves the dependency-group problem unsolved and forces every
    contributor to maintain a separate venv strategy.
  - **Hatch / PDM** — Both are good. `uv` won on raw speed and on
    the fact that the Astral team also ships `ruff`, which keeps the
    toolchain mental model small.
