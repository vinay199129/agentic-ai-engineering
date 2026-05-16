# agentic-ai-engineering

> A hands-on portfolio of agentic AI engineering — every major RAG technique, every major agent framework, human-in-the-loop patterns, indexing internals, evals, MCP, and deployment — all in one place, all runnable.

[![Lint](https://img.shields.io/badge/lint-ruff-blue)](#)
[![Types](https://img.shields.io/badge/types-mypy%20strict-blue)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-building%20in%20public-orange)](#)

This is a **learning-first hub repo**. Each topic area is a folder with runnable notebooks, a small demo app, and committed eval snapshots so progress and tradeoffs are reviewable in git. Two flagship deep-dive repos prove the same skills in production form:

- 🚀 **[`production-rag-pipeline`](../production-rag-pipeline)** — production hybrid RAG with self-hosted Langfuse, RAGAS regression in CI, Streamlit chat, Fly.io deploy
- 🤖 **[`multi-agent-research-system`](../multi-agent-research-system)** — LangGraph supervisor + 5 specialists, HITL approval gates, MCP-only tools, Postgres checkpointer with time-travel

---

## 🧭 Quick navigation

| Topic | Folder | What's inside |
|---|---|---|
| Foundations | [`00-foundations/`](00-foundations/) | Structured outputs, function calling, streaming, the 5 Anthropic workflow patterns |
| RAG | [`01-rag/`](01-rag/) | 13 techniques: naive → contextual chunking → hybrid → rerank → HyDE → Self-RAG → CRAG → Agentic → GraphRAG → Multimodal → Long-context |
| Indexing | [`02-indexing/`](02-indexing/) | Vector DB comparison + HNSW from scratch + IVF-PQ + BM25 + ColBERT + KG |
| Agentic frameworks | [`03-agentic-frameworks/`](03-agentic-frameworks/) | ReAct from scratch + LangGraph + Pydantic AI + CrewAI + MS Agent Framework + OpenAI Agents SDK + Smolagents + comparison |
| Human-in-the-loop | [`04-human-in-the-loop/`](04-human-in-the-loop/) | Interrupt/resume, approval gates, edit state, time-travel, async HITL via queue |
| Evals & observability | [`05-evals-and-observability/`](05-evals-and-observability/) | RAGAS (RAG + agent metrics), self-hosted Langfuse, LLM-as-judge, synthetic data, regression suite, cost/latency bench |
| MCP | [`06-mcp/`](06-mcp/) | Server, client, resources, custom MCP for a real API |
| Deployment | [`07-deployment-patterns/`](07-deployment-patterns/) | FastAPI streaming, Streamlit template, Docker compose, HF Spaces, Vercel AI SDK chat (TypeScript) |

---

## 🎯 Skills matrix *(populated as phases ship)*

| Skill | Where to see it |
|---|---|
| RAG pipeline design | `01-rag/`, `production-rag-pipeline` |
| Vector-DB selection & benchmarking | `02-indexing/00-vector-db-comparison/` |
| Index internals (HNSW, IVF-PQ) | `02-indexing/01-hnsw-deep-dive/`, `02-indexing/02-ivf-pq-quantization/` |
| Stateful agents (LangGraph) | `03-agentic-frameworks/01-langgraph/`, `multi-agent-research-system` |
| Type-safe agents (Pydantic AI) | `03-agentic-frameworks/02-pydantic-ai/` |
| Multi-agent orchestration | `03-agentic-frameworks/03-crewai/`, `multi-agent-research-system` |
| HITL workflow design | `04-human-in-the-loop/`, `multi-agent-research-system` |
| Eval-driven development | `05-evals-and-observability/`, both deep-dives |
| Observability (Langfuse) | `05-evals-and-observability/02-langfuse-tracing/`, both deep-dives |
| MCP server + client | `06-mcp/`, `multi-agent-research-system` |
| FastAPI streaming + SSE | `07-deployment-patterns/00-fastapi-streaming-agent/` |
| Containerized deploy | `07-deployment-patterns/02-docker-compose-stack/`, `production-rag-pipeline` |
| TypeScript / edge | `07-deployment-patterns/04-ts-vercel-ai-sdk-chat/` |

---

## 🚀 Getting started

```bash
# 1. Clone
git clone <repo-url> && cd agentic-ai-engineering

# 2. Install uv (https://docs.astral.sh/uv/), then:
uv sync --group dev

# 3. Copy env template (most folders work without API keys via cached LLM responses)
cp .env.example .env

# 4. Install pre-commit hooks
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg

# 5. Pick a folder, open its notebook, run.
```

Per-topic dependencies are installed on demand:

```bash
uv sync --group rag        # installs RAG-specific deps
uv sync --group frameworks # installs all agentic frameworks
# ... etc. See pyproject.toml [dependency-groups]
```

---

## 🗺️ Learning path

Recommended traversal order for someone learning end-to-end:

1. **`00-foundations/`** — structured outputs + function calling + the 5 workflow patterns
2. **`01-rag/00-naive-rag`** → **`01-rag/04-reranking`** — get a real RAG pipeline working
3. **`05-evals-and-observability/00-ragas-rag-eval`** — learn to measure before going further
4. **`01-rag/05-query-transformation`** → **`01-rag/12-comparison-bench`** — advanced RAG with measurement
5. **`02-indexing/`** — go deep on what's actually happening under the embeddings
6. **`03-agentic-frameworks/00-react-from-scratch`** then **`01-langgraph`**
7. **`04-human-in-the-loop/`** — make agents production-safe
8. **`06-mcp/`** — modern tool integration
9. **`07-deployment-patterns/`** — ship it

Full docs: see [`docs/learning-path.md`](docs/learning-path.md).

---

## 🛠️ Conventions

- **Notebooks** are the teaching artifact — code and markdown intuition stay in sync (see [`CONTRIBUTING.md`](CONTRIBUTING.md)).
- **Eval snapshots** (`eval-snapshot.json`) are committed for every folder that has measurable behavior so improvements/regressions are reviewable in git.
- **No API keys ever in cells.** Use `os.getenv(...)` + `.env`.
- **Conventional commits** enforced via `pre-commit`.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full leaf-folder template.

---

## 📦 Status

**Phases 0–2 complete.** Foundations + 13 RAG techniques + shared infra + eval pipeline are all in. See [`PLAN.md`](PLAN.md) for the full roadmap and [`01-rag/README.md`](01-rag/README.md) for the live leaderboard.

Building in public — follow along on:
- LinkedIn: *(link)*
- Twitter/X: *(link)*

---

## 🪪 License

MIT — see [`LICENSE`](LICENSE).
