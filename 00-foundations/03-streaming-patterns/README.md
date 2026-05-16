# Streaming patterns

**Problem:** Users feel first-token latency, not total latency. Blocking the UI until a 30-token answer completes is a UX bug.

**What you'll learn:**
- Three streaming shapes: synchronous token loops, async generators, and partial-JSON progressive parsing.
- The SSE wire format every major provider uses (and how `litellm.completion(..., stream=True)` abstracts it).
- A tiny tolerant JSON parser that surfaces fields the moment they complete, instead of blocking on the closing brace.
- When NOT to stream (short responses, strict validation pipelines, log sinks that hate deltas).

**When to use it:** Any user-facing response > ~200 chars, multi-step agents where intermediate output is useful, anywhere progressive UI matters.

**When NOT to use it:** Short responses, batch jobs, when downstream consumers can't handle deltas.

## Run it

```powershell
uv sync --group foundations
uv run jupyter lab 00-foundations/03-streaming-patterns/notebook.ipynb
```

The notebook simulates streaming offline by chunking a cached response; the live-mode code paths use `litellm.completion(..., stream=True)`.

## References

- [Server-Sent Events spec (WHATWG)](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [LiteLLM streaming guide](https://docs.litellm.ai/docs/completion/stream)
- [Anthropic streaming docs](https://docs.anthropic.com/en/api/streaming)
