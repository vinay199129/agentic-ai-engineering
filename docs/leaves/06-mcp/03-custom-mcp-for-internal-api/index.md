!!! info "`06-mcp/03-custom-mcp-for-internal-api`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/vinay199129/agentic-ai-engineering/tree/main/06-mcp/03-custom-mcp-for-internal-api)

**Headline metrics:** _no headline metric_

# Custom MCP for an internal API — wrap any HTTP service

**Problem:** Most internal APIs are not LLM-shaped: their endpoints take dozens of params, return verbose JSON, and assume the caller already knows the domain. Wrapping them in MCP gives you a chance to design the *agent-facing* surface — fewer endpoints, friendlier types, opinionated defaults — without touching the underlying service.

**What you'll learn:**
- The adapter pattern: thin MCP tool → calls the real HTTP API → returns trimmed JSON.
- Why you should make MCP tools **idempotent and parameter-light** even if the backing API isn't.
- Schema rewriting: hide enums the LLM doesn't need, expose only the parameters that affect outputs.
- A reusable retry/rate-limit decorator that lives at the MCP layer so every wrapped API gets it.

**When to use it:** Any time you'd otherwise paste an OpenAPI spec into the system prompt. The wrap is cheaper and safer.

**When NOT to use it:** APIs that are already small + LLM-friendly (most search APIs).

## Run it

```powershell
uv run jupyter lab 06-mcp/03-custom-mcp-for-internal-api/notebook.ipynb
uv run python 06-mcp/03-custom-mcp-for-internal-api/eval.py
```

The eval uses a **simulated** internal weather API (in-process, deterministic
fixtures) so no network access is required. The wrapping pattern is identical
for a real HTTP API.

## Key results

The eval issues a known set of weather queries, asserts the wrap correctly
sanitises ambiguous units, returns trimmed payloads, and rate-limit-rejects
overage. Tracked metrics: `wrap_call_success_rate`,
`payload_trim_ratio` (1 - bytes_returned / bytes_upstream),
`rate_limit_enforcement_rate`, `avg_latency_ms`.

## References

- [FastMCP HTTP wrapping recipes](https://github.com/jlowin/fastmcp)
- [How to design LLM-friendly APIs](https://www.anthropic.com/research/building-effective-agents)
