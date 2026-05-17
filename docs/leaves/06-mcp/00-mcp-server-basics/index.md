!!! info "`06-mcp/00-mcp-server-basics`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/vinay199129/agentic-ai-engineering/tree/main/06-mcp/00-mcp-server-basics)

**Headline metrics:** `canonical_method_coverage`=1 · `schema_validity_rate`=1

# MCP server basics — three tools, fully wired

**Problem:** Every agent framework reinvents tool calling. The Model Context Protocol (MCP) standardises it: one server, one JSON-RPC dialect, any compliant client. Once your tools live behind MCP they're reusable across LangChain, OpenAI Agents SDK, Claude Desktop, Cursor — anywhere that speaks the protocol.

**What you'll learn:**
- The four canonical MCP methods you must implement: `initialize`, `tools/list`, `tools/call`, plus optional `resources/*` and `prompts/*`.
- How tool input schemas (JSON Schema) become the contract between server and client.
- Why the spec separates `content` blocks from raw payloads — it future-proofs for images and embeddings.
- The 200-line server in `06-mcp/mcp_core.py` so you can see exactly what FastMCP wraps.

**When to use it:** Any tool you'd otherwise hard-wire into one agent. Even for a single agent, MCP gives you a free audit log and a clean separation between agent code and tool code.

**When NOT to use it:** One-off scripts; MCP framing adds latency you don't need.

## Run it

```powershell
uv run jupyter lab 06-mcp/00-mcp-server-basics/notebook.ipynb
uv run python 06-mcp/00-mcp-server-basics/eval.py
```

## Key results

The eval drives the server through every canonical method (`initialize`,
`tools/list`, `tools/call` × 3), checks all schemas validate, and asserts the
audit log has one entry per request. Tracked metrics:
`canonical_method_coverage`, `tool_call_success_rate`, `schema_validity_rate`,
`avg_latency_ms`.

## References

- [Model Context Protocol spec](https://modelcontextprotocol.io/specification/2025-06-18)
- [FastMCP — production Python framework](https://github.com/jlowin/fastmcp)
- [JSON-RPC 2.0](https://www.jsonrpc.org/specification)
