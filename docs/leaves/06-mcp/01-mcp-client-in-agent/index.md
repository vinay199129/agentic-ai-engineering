!!! info "`06-mcp/01-mcp-client-in-agent`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/vinay199129/agentic-ai-engineering/tree/main/06-mcp/01-mcp-client-in-agent)

**Headline metrics:** `tool_call_accuracy`=1 · `final_answer_grounded`=0.333

# MCP client in an agent — `tools/call` from a real loop

**Problem:** Wiring a tool registry into an agent framework is per-framework drudgery. With MCP, the agent only needs an MCP client — pointing it at a different server is enough to swap the whole tool palette. This leaf shows the canonical adapter pattern: `client.list_tools()` becomes the LLM tool list; `client.call_tool(name, args)` is the only execution path.

**What you'll learn:**
- The adapter loop: `list_tools` → expose to LLM → on tool call → `call_tool` → feed result back.
- Why MCP's tool result shape (`content` blocks) maps cleanly onto LangGraph / OpenAI Agents SDK message shapes.
- How the agent in this leaf is byte-identical to the `03-agentic-frameworks/00-react-from-scratch` baseline except for tool transport.
- Measuring tool-call accuracy on the same shared corpus task so MCP-vs-native is apples-to-apples.

**When to use it:** Any agent you want to ship to many hosts (Claude Desktop, Cursor, custom UI) without re-implementing tool calling per host.

**When NOT to use it:** Throwaway scripts; native function calling is two lines shorter.

## Run it

```powershell
uv run jupyter lab 06-mcp/01-mcp-client-in-agent/notebook.ipynb
uv run python 06-mcp/01-mcp-client-in-agent/eval.py
```

## Key results

Same three-question demo set as `03-agentic-frameworks/`. Tracked metrics:
`tool_call_accuracy`, `final_answer_grounded`, `avg_n_steps`,
`avg_latency_ms` — directly comparable to the framework tour snapshots.

## References

- LangChain MCP adapter: [`langchain-mcp-adapters`](https://github.com/langchain-ai/langchain-mcp-adapters)
- OpenAI Agents SDK MCP support: [docs](https://github.com/openai/openai-agents-python)
