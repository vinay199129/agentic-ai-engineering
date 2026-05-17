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
| Find the HITL mini-LangGraph | [`04-human-in-the-loop/hitl.py`](04-human-in-the-loop/hitl.py) (`Graph`, `Checkpointer.fork`, `Interrupt`, `Command`, `stream_events`, `build_research_graph`, `run_scenario`) |
| Find the in-process MCP server/client | [`06-mcp/mcp_core.py`](06-mcp/mcp_core.py) (`Server`, `Client`, `build_corpus_server`, `mcp_agent_solve`) |
| Find the shared framework task | [`03-agentic-frameworks/task.py`](03-agentic-frameworks/task.py) (`search_corpus`, `fetch_paper`, `cite`, `run_evaluation`) |
| Find the FastAPI streaming agent pattern | [`07-deployment-patterns/00-fastapi-streaming-agent/`](07-deployment-patterns/00-fastapi-streaming-agent/) |
| Find the canonical corpus | `benchmarks/corpus/` (download script only; data git-ignored) |
| Find golden Q&A | `benchmarks/golden-qa/` |
| See eval results | every leaf's `eval-snapshot.json`; rolled up in `01-rag/12-comparison-bench/` and [`docs/leaderboard.md`](docs/leaderboard.md) |
| Re-build the dashboard + leaderboard | `uv run python scripts/build_dashboard.py` (re-aggregates every `eval-snapshot.json`) |
| Re-build the in-browser notebook site | `uv run python scripts/build_jupyterlite.py` → outputs `site/lite/` |
| Read deep-dive write-ups | [`docs/deep-dives/`](docs/deep-dives/) — five long-form articles |
| Read architecture decision records | [`docs/architecture-decisions/`](docs/architecture-decisions/) — six ADRs |
| Run CI locally | `uv run ruff check . && uv run mypy . && uv run pytest` |

## Dependency groups (`pyproject.toml` `[dependency-groups]`)

`dev`, `rag`, `indexing`, `frameworks`, `evals`, `hitl`, `mcp`, `deployment`.
Install only what a leaf needs: `uv sync --group hitl` etc. CI installs every
group so lint / type-check / pytest see all the source.

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
