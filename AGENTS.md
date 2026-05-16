# AGENTS.md

> Navigation guide for LLM agents (Copilot, Claude Code, Cursor, etc.) working in this repo.

## Repo purpose

A hub portfolio for agentic AI engineering. Learning-first, notebook-heavy, with committed eval snapshots and two production-grade deep-dive repos linked from the README.

## Where things live

| If you need to… | Look here |
|---|---|
| Understand the overall roadmap | [`PLAN.md`](PLAN.md) |
| Add a new technique | Read [`CONTRIBUTING.md`](CONTRIBUTING.md) → "Adding a new technique" |
| Find shared utilities | `shared/` (LLM shim, loaders, prompts, evaluators) |
| Find the canonical corpus | `benchmarks/corpus/` (download script only; data git-ignored) |
| Find golden Q&A | `benchmarks/golden-qa/` |
| See eval results | every leaf's `eval-snapshot.json`; rolled up in `01-rag/12-comparison-bench/` |
| Run CI locally | `uv run ruff check . && uv run mypy . && uv run pytest` |

## Conventions you must follow

1. **Notebooks: code and markdown cells stay in sync.** If you change a hyperparameter, update the explanatory markdown.
2. **No API keys in cells.** Always `os.getenv(...)` + `.env`.
3. **Use the shared LLM shim** at `shared/llm.py` so notebooks run on any provider.
4. **Commit eval snapshots** after meaningful changes. CI compares against `main` and fails on > 5% regression.
5. **Conventional commits.** Pre-commit hook enforces this.
6. **Per-topic dependency groups.** New runtime deps go in `pyproject.toml` `[dependency-groups]`, not in the root `dependencies`.

## Things to avoid

- Don't add a leaf folder without a `README.md` and (if applicable) an `eval.py` + snapshot.
- Don't reformat unrelated files when making a change.
- Don't introduce a new framework dependency without updating the relevant comparison folder.
- Don't add notebooks that require API keys to execute in CI — use cached responses (the LLM shim handles this when `LLM_CACHE_ONLY=1`).

## Related repos

- [`production-rag-pipeline`](../production-rag-pipeline) — production RAG deep-dive
- [`multi-agent-research-system`](../multi-agent-research-system) — multi-agent + HITL deep-dive
