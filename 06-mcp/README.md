# 06 — MCP (Model Context Protocol)

The 2026 standard for connecting agents to tools, resources, and prompts.

## Planned leaves

| Leaf | Topic | Status |
|---|---|---|
| `00-mcp-server-basics/` | Python FastMCP server exposing 3 tools | ✅ |
| `01-mcp-client-in-agent/` | LangGraph agent consuming MCP tools | ✅ |
| `02-mcp-with-resources/` | Resources + prompts (not just tools) | ✅ |
| `03-custom-mcp-for-internal-api/` | Wrap an internal HTTP API behind an LLM-friendly MCP surface | ✅ |

## Shared module

`mcp_core.py` is a pure-Python in-process JSON-RPC 2.0 MCP server + client
(no external deps). It implements the canonical methods (`initialize`,
`tools/{list,call}`, `resources/{list,read}`, `prompts/{list,get}`) and
ships with `build_corpus_server(with_resources, with_prompts)` so every
leaf shares the same demo surface and snapshots remain comparable.
