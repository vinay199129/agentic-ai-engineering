# Langfuse-style tracing — spans, scores, in-memory recorder

**Problem:** Print-debugging an LLM agent stops scaling at about three tool calls. You need *traces* — nested spans with inputs, outputs, timings, and per-span quality scores. Langfuse is the open-source self-hosted answer; this leaf shows the trace-shape conventions and how to wire them in without requiring a running Langfuse server.

**What you'll learn:**
- **Span anatomy** — `name`, `input`, `output`, `start`, `end`, parent chain.
- **Score anatomy** — numeric / boolean / categorical scores attached to spans.
- A tiny **in-memory recorder** with the same shape as `langfuse.Langfuse` so notebooks work offline; swap in the real client by changing one import.
- How to score retrieval and generation spans for an end-to-end RAG trace.

**When to use it:** Any agent that does ≥ 2 LLM/tool calls per request. Tracing is cheaper than debugging blind.

**When NOT to use it:** Pure stateless completions where you don't care about provenance — log latency and cost in metrics instead.

## Run it

```powershell
uv sync --group evals
uv run jupyter lab 05-evals-and-observability/02-langfuse-tracing/notebook.ipynb
uv run python 05-evals-and-observability/02-langfuse-tracing/eval.py
```

The notebook runs entirely on an in-memory recorder. To switch to the real self-hosted Langfuse:

```python
# notebook
# from langfuse import Langfuse
# tracer = Langfuse(host="http://localhost:3000", public_key=..., secret_key=...)
from recorder import InMemoryTracer
tracer = InMemoryTracer()
```

Deploying real Langfuse will be covered in `07-deployment-patterns/02-docker-compose-stack/` in Phase 8.

## Key results

See [`eval-snapshot.json`](./eval-snapshot.json) for trace-structure invariants (n_spans, n_scores, ordering correctness, average span duration) on a 3-question demo run.

## References

- [Langfuse — self-hosted observability for LLM apps](https://langfuse.com/)
- [OpenTelemetry semantic conventions for LLM traces (draft)](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
- Phoenix / Arize — alternative open-source LLM tracing stacks
