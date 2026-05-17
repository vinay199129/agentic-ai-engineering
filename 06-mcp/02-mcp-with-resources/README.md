# MCP with resources and prompts — beyond just tools

**Problem:** Most MCP servers expose only tools — losing two of the three first-class concepts in the spec. **Resources** give the LLM stable, addressable context (URIs like `arxiv://synth-001`); **prompts** package reusable system-prompt templates with their arguments. Together they let you ship an MCP server that's a true *application surface* — the agent can browse what's available, not just guess at it.

**What you'll learn:**
- How to register a resource (URI, mime-type, text/binary content).
- How clients enumerate (`resources/list`) and fetch (`resources/read`) — and why URIs beat tool-call IDs for caching.
- Registering a parameterised prompt with `arguments`, and rendering it server-side so clients can't drift from the canonical template.
- Why MCP's three primitives map cleanly onto LangChain's `Tool`, `Document`, and `PromptTemplate`.

**When to use it:** Servers that expose a *corpus* (docs, configs, schemas) as well as actions; production agents where the system prompt itself should be versioned & owned by the server.

**When NOT to use it:** Single-purpose tools.

## Run it

```powershell
uv run jupyter lab 06-mcp/02-mcp-with-resources/notebook.ipynb
uv run python 06-mcp/02-mcp-with-resources/eval.py
```

## Key results

The eval registers a resource per paper + one parameterised prompt; checks
the three list-methods agree on the cardinality the server reports, that
every advertised URI is readable, and that the rendered prompt has the
expected roles. Tracked metrics: `resource_read_success_rate`,
`prompt_render_validity`, `resource_uri_uniqueness`, `avg_latency_ms`.

## References

- [MCP — Resources](https://modelcontextprotocol.io/docs/concepts/resources)
- [MCP — Prompts](https://modelcontextprotocol.io/docs/concepts/prompts)
