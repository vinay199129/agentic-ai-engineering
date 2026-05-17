!!! info "`00-foundations/02-function-calling`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/vinay199129/agentic-ai-engineering/tree/main/00-foundations/02-function-calling)

# Function calling

**Problem:** You need the LLM to *call code* — fetch data, mutate state, hand off to a tool — and want it routed reliably, not via brittle regex on free-form text.

**What you'll learn:**
- Native tool/function calling (`tools=[{...}]`) — single tool, multi-tool, parallel calls.
- Manual JSON-schema-instructed prompting as a portable fallback when a provider lacks the native API.
- How tool *schemas* hash into the cache key — changing a schema invalidates cached responses (this is correct).
- The exact assistant / tool message dance the provider expects on the round-trip after a tool call.

**When to use it:** Anytime the model needs to act outside the chat window — search, calculator, retrieval, database, API call.

**When NOT to use it:** When a pure prompt with structured output is enough and you don't actually need to execute anything.

## Run it

```powershell
uv sync --group foundations
uv run jupyter lab 00-foundations/02-function-calling/notebook.ipynb
```

Runs offline by default (`LLM_CACHE_ONLY=1`); set an API key in `.env` to call live.

## References

- [OpenAI function calling guide](https://platform.openai.com/docs/guides/function-calling)
- [Anthropic tool use](https://docs.anthropic.com/en/docs/tool-use)
- [LiteLLM tool calling](https://docs.litellm.ai/docs/completion/function_call)
