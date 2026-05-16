# shared/

Common utilities reused across topic folders. **Avoid bloat** — only put something here when it's used by ≥ 2 leaves.

## Planned modules *(populated as phases need them)*

| Module | Purpose | Lands in |
|---|---|---|
| `llm.py` | `litellm`-based shim with cached-response mode for CI | Phase 1 |
| `loaders.py` | Corpus loaders (arxiv PDFs, JSONL Q&A) | Phase 1 |
| `prompts.py` | Reusable prompt templates | Phase 1 |
| `evaluators.py` | RAGAS wrappers + custom evaluators | Phase 4 |
| `cache.py` | On-disk LLM response cache for `LLM_CACHE_ONLY` mode | Phase 1 |
| `tracing.py` | Langfuse client bootstrap | Phase 4 |

## Conventions

- Strict types (`mypy --strict`).
- Async-first for I/O.
- Pure functions over classes when state isn't needed.
- Pydantic for any data shape that crosses a boundary.
