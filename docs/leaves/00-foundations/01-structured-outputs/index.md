!!! info "`00-foundations/01-structured-outputs`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/vinay199129/agentic-ai-engineering/tree/main/00-foundations/01-structured-outputs)

# Structured outputs

**Problem:** Free-form LLM text breaks every downstream consumer. You want a typed object you can `.field` into without `try/except` around every `json.loads`.

**What you'll learn:**
- Native structured outputs (`response_format={"type": "json_schema", ...}`) vs. JSON mode vs. instructed prompting.
- Using Pydantic models as the schema source — define once, validate everywhere.
- When models still hallucinate fields that aren't in the schema (and what to do about it).
- Handling partial / streamed structured outputs (forward reference to `03-streaming-patterns`).
- Cost & latency tradeoffs across the three approaches.

**When to use it:** Any time the consumer of the response isn't a human — extraction pipelines, function calling, agent state, evaluation harnesses.

**When NOT to use it:** Conversational UIs where you want the model's voice unconstrained.

## Run it

```powershell
uv sync --group foundations
uv run jupyter lab 00-foundations/01-structured-outputs/notebook.ipynb
```

The notebook ships pre-seeded LLM cache entries; it executes offline with `LLM_CACHE_ONLY=1`.

## References

- [OpenAI structured outputs guide](https://platform.openai.com/docs/guides/structured-outputs)
- [Anthropic tool use](https://docs.anthropic.com/en/docs/tool-use)
- [Pydantic JSON schema reference](https://docs.pydantic.dev/latest/concepts/json_schema/)
