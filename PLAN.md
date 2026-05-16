# PLAN — `agentic-ai-engineering` (Hub Repo)

> Hub monorepo for the agentic-AI-engineer portfolio. Houses all learning content, notebooks, and small demos across 8 topic areas. Cross-links to the two flagship deep-dive repos.

---

## Portfolio Context (all 3 repos)

| # | Repo | Role | Folder |
|---|---|---|---|
| 1 | **`agentic-ai-engineering`** *(this one)* | Hub: learning-first monorepo, notebooks + small demos across all topics | `C:\Project Files\agentic-ai-engineering\` |
| 2 | `production-rag-pipeline` | Deep-dive: production hybrid RAG with evals/observability/CI/CD | `C:\Project Files\production-rag-pipeline\` |
| 3 | `multi-agent-research-system` | Deep-dive: LangGraph supervisor + HITL gates + MCP tools | `C:\Project Files\multi-agent-research-system\` |

Recruiters land on the hub README, see a skills matrix, and click through to either a notebook (depth) or a deep-dive repo (production proof).

---

## Hub Repo — Role & Audience

- **Role:** "Show what I know" — every major RAG technique, every major agentic framework, HITL patterns, indexing internals, evals, MCP, deployment.
- **Audience:** Recruiters scanning for keywords + engineers wanting to actually learn.
- **Style:** Notebook-first (code + markdown intuition together), small Streamlit/Gradio demos where they add value, RAGAS metric snapshots committed to git so trends are reviewable.
- **Languages:** Python 3.12+ (`uv` workspace) primary; 1 TypeScript sub-project in `07-deployment-patterns/04-ts-vercel-ai-sdk-chat` for stack breadth.

---

## Folder Layout

```
agentic-ai-engineering/
├── README.md                       # Portfolio landing: hero, demo links, skills matrix, learning path
├── AGENTS.md                       # How an LLM agent should navigate this repo (meta-touch)
├── CONTRIBUTING.md                 # Leaf-folder template, conventions, eval-snapshot rules
├── pyproject.toml                  # uv workspace root
├── .github/workflows/              # Lint, type-check, eval-regression, nbconvert-execute on PR
├── docs/                           # MkDocs Material → GitHub Pages
│   ├── index.md
│   ├── learning-path.md            # Recommended traversal order
│   ├── skills-matrix.md
│   └── architecture-decisions/     # ADRs for non-obvious choices
├── benchmarks/                     # Shared eval datasets + leaderboards consumed across folders
│   ├── corpus/                     # Canonical arxiv-cs.CL ~500-doc corpus (download script, not data)
│   ├── golden-qa/                  # Hand-curated Q&A pairs
│   └── synthetic-qa/               # RAGAS-generated test sets
├── shared/                         # Common utilities (loaders, prompts, evaluators, litellm shim)
├── 00-foundations/
│   ├── 01-structured-outputs/      # Pydantic + tool schemas + JSON-mode comparison
│   ├── 02-function-calling/        # Native vs JSON-schema vs Pydantic AI
│   ├── 03-streaming-patterns/      # SSE, async generators, partial JSON parsing
│   └── 04-prompt-patterns/         # Anthropic's 5: prompt chain, routing, parallelization, orchestrator-workers, evaluator-optimizer
├── 01-rag/
│   ├── 00-naive-rag/               # Baseline: chunk → embed → top-k → stuff
│   ├── 01-chunking-strategies/     # Fixed, recursive, semantic, propositional, contextual (Anthropic)
│   ├── 02-embedding-comparison/    # OpenAI, Cohere, BGE, Voyage, Nomic, mxbai
│   ├── 03-hybrid-search/           # BM25 + dense + RRF fusion
│   ├── 04-reranking/               # Cohere Rerank, BGE reranker, ColBERT late interaction
│   ├── 05-query-transformation/    # HyDE, multi-query, step-back, decomposition
│   ├── 06-self-rag/                # Self-reflection tokens / self-grading
│   ├── 07-corrective-rag/          # CRAG: retrieval grader + web fallback
│   ├── 08-agentic-rag/             # Router + tool-calling retrieval
│   ├── 09-graph-rag/               # Microsoft GraphRAG: entity/community extraction
│   ├── 10-multimodal-rag/          # Image + text via ColPali / Voyage Multimodal
│   ├── 11-long-context-rag/        # Contextual retrieval + cache-augmented
│   └── 12-comparison-bench/        # Side-by-side eval table on shared corpus
├── 02-indexing/
│   ├── 00-vector-db-comparison/    # pgvector, Qdrant, Chroma, LanceDB, Weaviate, Milvus (matrix + benchmark)
│   ├── 01-hnsw-deep-dive/          # Build HNSW from scratch in numpy; visualize layers
│   ├── 02-ivf-pq-quantization/     # FAISS IVF-PQ; recall vs memory tradeoff
│   ├── 03-bm25-and-hybrid/         # rank_bm25 + dense, RRF, weighted fusion
│   ├── 04-knowledge-graph-index/   # Neo4j + LlamaIndex KG indexer
│   ├── 05-summary-tree-index/      # LlamaIndex hierarchical summarization
│   ├── 06-colbert-late-interaction/ # PLAID / RAGatouille
│   └── 07-incremental-indexing/    # Delta indexing, deletes, re-embed strategies
├── 03-agentic-frameworks/
│   ├── 00-react-from-scratch/      # Pure-Python ReAct; no framework — proves fundamentals
│   ├── 01-langgraph/               # Stateful graphs, checkpointer, subgraphs, supervisor
│   ├── 02-pydantic-ai/             # Type-safe agents, dependencies, structured deps
│   ├── 03-crewai/                  # Roles, tasks, hierarchical crews
│   ├── 04-microsoft-agent-framework/ # Sequential/concurrent/group-chat workflows
│   ├── 05-openai-agents-sdk/       # Handoffs, guardrails, sessions
│   ├── 06-smolagents/              # Code-as-action agents (HuggingFace)
│   └── 07-framework-comparison/    # Same task → 6 implementations + tradeoff matrix
├── 04-human-in-the-loop/
│   ├── 00-interrupt-and-resume/    # LangGraph `interrupt()` + resume with Command
│   ├── 01-approval-gates/          # Tool-call approval pattern
│   ├── 02-edit-state/              # Inspect & modify graph state mid-run
│   ├── 03-time-travel-debug/       # Checkpoint rewind / fork
│   ├── 04-streaming-with-intervention/ # Pause stream → user input → resume
│   └── 05-async-hitl-via-queue/    # Long-running agent + email/Slack approval webhook
├── 05-evals-and-observability/
│   ├── 00-ragas-rag-eval/          # Faithfulness, Context Precision/Recall, Answer Relevancy
│   ├── 01-ragas-agent-eval/        # Tool Call Accuracy, Agent Goal Accuracy, Topic Adherence
│   ├── 02-langfuse-tracing/        # Self-hosted Langfuse + spans + scores
│   ├── 03-llm-as-judge/            # Rubric-based; pairwise; bias mitigation
│   ├── 04-synthetic-eval-data/     # RAGAS Testset Generator over the canonical corpus
│   ├── 05-regression-suite/        # pytest + GH Actions; fail PR on metric drop
│   └── 06-cost-and-latency-bench/  # Token + ms tracking across models
├── 06-mcp/
│   ├── 00-mcp-server-basics/       # Python FastMCP server exposing 3 tools
│   ├── 01-mcp-client-in-agent/     # LangGraph agent consuming MCP tools
│   ├── 02-mcp-with-resources/      # Resources + prompts (not just tools)
│   └── 03-custom-mcp-for-internal-api/ # Real-world wrap (e.g., GitHub or weather API)
└── 07-deployment-patterns/
    ├── 00-fastapi-streaming-agent/ # SSE endpoint, auth, rate limit
    ├── 01-streamlit-demo-template/ # Reusable shell for HF Spaces
    ├── 02-docker-compose-stack/    # API + Postgres + pgvector + Langfuse + Redis
    ├── 03-hf-spaces-deploy/        # CI-driven push
    └── 04-ts-vercel-ai-sdk-chat/   # TypeScript chat UI streaming from FastAPI backend
```

---

## Per-Leaf-Folder Conventions

Every leaf folder ships:

1. `README.md` — Problem, what you'll learn, when to use, references, link back to hub
2. `notebook.ipynb` — Teaching artifact: code cells + markdown intuition (kept in sync per user's `notebook-editing.md` preference)
3. `app.py` — Small Streamlit/Gradio demo when it adds value
4. `tests/` — `pytest` for reusable code
5. `eval.py` — Produces `eval-snapshot.json` (RAGAS or custom evaluator). Snapshots committed → trends reviewable.
6. Dependency declaration via `uv` workspace member `pyproject.toml`

---

## Hub Phases (Phases 0–8, 11 — deep-dives covered in their own plans)

### Phase 0 — Scaffolding *(prerequisite)*

- Init `agentic-ai-engineering` as a git repo, MIT LICENSE, conventional-commits config, `.gitignore`
- Set up `uv` workspace; root `pyproject.toml` with `ruff` + `mypy --strict` + `pytest` + `nbconvert`
- Write `CONTRIBUTING.md` documenting leaf-folder template + eval-snapshot rules
- Set up MkDocs Material → GitHub Pages (`docs/`) with empty index + learning-path stub
- Baseline `.github/workflows/`: `lint.yml` (ruff + mypy), `notebooks.yml` (nbconvert --execute with mocked LLM responses)
- Top-level `README.md` skeleton: hero, demo links placeholder, skills matrix placeholder

### Phase 1 — Foundations + Naive RAG *(parallel-safe after 0)*

- Implement `00-foundations/` all 4 subfolders
- Implement `01-rag/00-naive-rag`, `01-chunking-strategies`, `02-embedding-comparison`
- Build `benchmarks/corpus/download.py` for arxiv-cs.CL (~500 papers, last 2 years)
- Build `benchmarks/golden-qa/` with ~30 hand-curated Q&A pairs

### Phase 2 — Advanced RAG *(depends on 1)*

- Implement `01-rag/03-hybrid-search` through `01-rag/11-long-context-rag`
- Each leaf emits an `eval-snapshot.json` consumed by `12-comparison-bench`
- Implement `12-comparison-bench/` producing a Markdown leaderboard table auto-generated from snapshots

### Phase 3 — Indexing Deep Dives *(parallel with 2)*

- Implement `02-indexing/` all 8 subfolders
- `00-vector-db-comparison/` produces a benchmark table: recall@10, p95 latency, $/1M vectors, ingestion time
- `01-hnsw-deep-dive/` includes a numpy reference implementation + matplotlib visualization of layered graph

### Phase 4 — Evals & Observability *(depends on 1)*

- Implement `05-evals-and-observability/` all 7 subfolders
- Stand up self-hosted Langfuse (Docker Compose snippet to be reused in `07-deployment-patterns/02-docker-compose-stack`)
- Wire `05-regression-suite/` into hub CI: PR fails if any `eval-snapshot.json` regresses > 5% vs. `main`

### Phase 5 — Agentic Frameworks Tour *(parallel with 3–4)*

- Implement `03-agentic-frameworks/00-react-from-scratch` first (sets the conceptual baseline)
- Choose one shared task (recommend: "Research and summarize a given arxiv paper with citations") and implement it in all 6 frameworks (LangGraph, Pydantic AI, CrewAI, Microsoft Agent Framework, OpenAI Agents SDK, Smolagents)
- Implement `07-framework-comparison/` with tradeoff matrix + opinionated commentary

### Phase 6 — HITL Patterns *(depends on LangGraph done in 5)*

- Implement `04-human-in-the-loop/` all 6 subfolders
- Primarily LangGraph (`interrupt()` + checkpointer), but include 1 CrewAI example for breadth
- `05-async-hitl-via-queue/` demonstrates email/Slack approval webhook with FastAPI

### Phase 7 — MCP *(parallel with 6)*

- Implement `06-mcp/` all 4 subfolders
- `00-mcp-server-basics/` uses FastMCP, exposes 3 tools (search, fetch, summarize)
- `01-mcp-client-in-agent/` shows the same LangGraph agent from Phase 5 calling MCP tools instead of native tools

### Phase 8 — Deployment Patterns *(depends on prior phases)*

- Implement `07-deployment-patterns/` all 5 subfolders
- Deploy 3–5 standout hub demos to HF Spaces (recommend: agentic-RAG, framework-comparison, multimodal-RAG)
- Implement `04-ts-vercel-ai-sdk-chat/` as TypeScript front-end streaming from a hub FastAPI backend

### Phase 11 — Portfolio Polish & Launch *(blocks on Phases 0–10 and both deep-dives)*

- Hub README final form: hero with demo screenshots, skills matrix mapping each folder → competencies, learning path, prominent links to both deep-dive repos
- Architecture diagrams (mermaid) embedded
- Blog-style write-ups in `docs/` for top 5 most impressive techniques (GraphRAG, Self-RAG vs CRAG, HNSW internals, framework comparison, MCP)
- `AGENTS.md` describing repo navigation for LLM agents
- Cross-link in both deep-dive READMEs back to hub
- Soft launch: Awesome-LLM lists, Hacker News, LinkedIn, Twitter

> **Phase 9 = `production-rag-pipeline` plan**
> **Phase 10 = `multi-agent-research-system` plan**

---

## Verification

**Automated (CI on every PR):**

- `ruff check` + `mypy --strict` pass across hub
- `pytest` passes for every leaf folder with reusable code
- `jupyter nbconvert --execute` runs every notebook end-to-end (using a `pytest-recording` / VCR-style cache of LLM responses to control cost)
- `eval-snapshot.json` regression check: PR fails if any leaf's snapshot regresses > 5%

**Portfolio-level (manual review):**

- Hub README scannable in < 60 seconds — recruiter identifies 5 impressive things
- Skills matrix maps every folder to claimed competencies
- All 3 repos cross-link
- Live demos reachable from hub README
- README renders correctly on GitHub mobile

---

## Scope

**Included:** notebooks + production code, self-hosted observability (no paid vendor required), 1 TS sub-project, MCP server + client, live demos, eval regression in CI, MkDocs Material site.

**Excluded:** training/fine-tuning (not an MLE portfolio), voice agents (defer as 4th deep-dive if wanted), mobile clients, self-hosted LLM inference (API providers only via `litellm` shim), paid vendor lock-in.

---

## Open Considerations

1. **Canonical corpus** — recommend arxiv-cs.CL last 2 years (~500 papers). Alternative: LangGraph's own docs (meta and clever).
2. **LLM provider strategy** — recommend `litellm` shim with OpenAI + Anthropic + one open model (Groq/Together) so cost-conscious viewers can run examples. Alternative: OpenAI-only.
3. **Shipping cadence** — recommend ship-in-public: publish hub Day 1 with Phase 0+1 done, add a phase every 1–2 weeks with social posts. Alternative: single big launch after Phase 11.
4. **Skills matrix in README** — recommend including; directly addresses recruiter pattern-matching.

---

## What "Pick This One" Means

When you say "let's do `agentic-ai-engineering`", I will start at **Phase 0** and produce all scaffolding files, then stop and confirm before moving to Phase 1. Each subsequent phase is its own focused conversation.
