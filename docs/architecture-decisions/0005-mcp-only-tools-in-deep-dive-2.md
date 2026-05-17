# 0005 — MCP-only tools in the multi-agent deep-dive

- **Status:** accepted
- **Date:** 2025-11-29
- **Context:** The multi-agent deep-dive repo
  (`multi-agent-research-system`) has a choice for how its agents
  call tools: (a) native function-calling tools registered directly
  on the agent runtime, or (b) routed through an MCP server. The
  hub's Phase 7 leaves show MCP works end-to-end and adds no
  measurable accuracy cost; this ADR records why we made MCP the
  *only* tool surface in the deep-dive.
- **Decision:** All tools the deep-dive agents call are exposed via
  an **MCP server** built on the `mcp_core.py` patterns from
  [`06-mcp/`](../leaves/06-mcp/index.md). The agent runtime knows nothing about
  individual tools — it knows only about the MCP server URL.
- **Consequences:**
  - **Good** — A single audit trail and single rate limiter for every
    tool call. Adding a new tool requires zero changes in the agent
    code. The system prompt becomes one paragraph because tool
    documentation is fetched via `tools/list` at session start.
  - **Good** — Proves MCP fluency end-to-end to readers and recruiters,
    which is a primary goal of the deep-dive.
  - **Bad** — MCP imposes a JSON-RPC hop per tool call. Trivial in
    cost for our workload (tens of tool calls per query); would matter
    in tight inner loops, which we don't have.
- **Alternatives considered:**
  - **Native tools only** — Faster to ship; loses the architectural
    win recorded in [the MCP deep-dive](../deep-dives/05-mcp.md).
  - **Hybrid (some native, some MCP)** — Two systems to reason about
    for no clear gain. Rejected.
