# Launch checklist

A practical, opinionated checklist for soft-launching the
`agentic-ai-engineering` portfolio. Everything below is **prepared
text + an ordered runbook** — the actual posting / DMs are yours to
do.

> Cross-linking from the two deep-dive repos (`production-rag-pipeline`,
> `multi-agent-research-system`) back to this hub still needs to be
> done in those repos. That work cannot happen from this repo's CI.

## Phase A — Pre-flight (do once)

- [ ] Push the latest `main` to GitHub. Verify the README hero renders
  correctly on github.com (mermaid blocks work natively).
- [ ] Set repository **About** sidebar: short description, topics
  `rag`, `agentic-ai`, `llm`, `langgraph`, `mcp`, `evals`, `python`,
  `portfolio`.
- [ ] Pin the three flagship repos on your GitHub profile:
  - `agentic-ai-engineering` (this hub)
  - `production-rag-pipeline`
  - `multi-agent-research-system`
- [ ] Enable GitHub Pages from `gh-pages` branch via the MkDocs build
  (`uv run mkdocs gh-deploy`). Verify nav covers learning path, skills
  matrix, deep-dives, ADRs.
- [ ] Run `uv run pytest && uv run ruff check . && uv run mypy .` one
  last time. Make sure CI is green.
- [ ] Open the Issues tab and pin a single issue titled
  "Where to start" pointing at the README "Reader paths" section.

## Phase B — The launch posts (templates)

### B1. Hacker News (Show HN)

> Title: **Show HN: agentic-ai-engineering — a notebook-driven hub
> for modern RAG, agents, and evals (with committed eval-snapshots)**

> Body:
>
> Hi HN. I built this hub to learn — and to *prove I learned* —
> the current generation of agentic AI engineering: RAG variants,
> indexing internals, every popular agent framework run on the same
> task, HITL patterns, MCP, evals, and deployment. ~50 leaf folders,
> each with a README, a runnable notebook, an `eval.py`, and a
> committed `eval-snapshot.json` that CI uses to fail PRs on > 5%
> regressions.
>
> Two production-grade deep-dive repos build on the hub:
> `production-rag-pipeline` and `multi-agent-research-system`. They
> reuse the hub's shared modules (the LLM shim, the HITL mini-
> LangGraph, the in-process MCP server) so everything runs offline
> in CI with cached responses.
>
> The thing I'd most welcome feedback on: the eval architecture in
> Phase 4 (`05-evals-and-observability/`). RAGAS-style metrics,
> agent metrics, judge, synthetic Q&A, regression suite — all
> implemented in-repo with deterministic fallbacks so CI runs with
> no API keys. Curious whether that pattern travels well to other
> people's projects.
>
> Repo: <https://github.com/your-handle/agentic-ai-engineering>

### B2. LinkedIn

> I've spent the last several months building
> **agentic-ai-engineering**: a hands-on hub portfolio covering
> modern RAG, indexing internals, every major agent framework, HITL,
> MCP, evals, and deployment patterns.
>
> ~50 runnable notebooks. Every leaf has a committed eval snapshot
> that CI compares against `main` and fails PRs on > 5% regressions.
> Two production-grade deep-dive repos build on top.
>
> Highlights:
> • Phase 1 — naive → advanced RAG (12 variants, each measured)
> • Phase 3 — vector indexing internals (HNSW, IVF, PQ from scratch)
> • Phase 5 — same agent task across 7 frameworks
> • Phase 6 — HITL patterns with a pure-Python mini-LangGraph
> • Phase 7 — MCP servers, resources, and prompts
> • Phase 8 — FastAPI + Streamlit + HF Spaces + Docker Compose +
>   Next.js streaming demo
>
> If you build or hire for agentic AI roles, the skills matrix in
> the README is the fastest way in.
>
> 🔗 <https://github.com/your-handle/agentic-ai-engineering>

### B3. X / Twitter thread

> 1/ Shipping **agentic-ai-engineering** today — a hub portfolio
> that taught me modern agentic AI by building every important
> pattern at least once. Notebook-driven, ~50 leaves, every leaf
> has a committed eval snapshot. Thread 👇

> 2/ Every folder ships the same four things: README, notebook,
> eval.py, eval-snapshot.json. CI compares against main and fails
> PRs on > 5% regressions. No more "the demo worked yesterday".

> 3/ Phase 1 builds naive RAG, then 12 advanced variants
> (HyDE, Self-RAG, CRAG, GraphRAG, multi-query, hybrid, rerank,
> long-context, RAPTOR, etc). Each one is a measurable delta
> against the baseline.

> 4/ Phase 3 implements HNSW, IVF, and PQ from scratch in NumPy.
> 150 lines of HNSW vs FAISS. The point isn't to compete — it's
> to *understand* `ef_search` the night you need to.

> 5/ Phase 5 runs the same agent task across 7 frameworks
> (ReAct from scratch, LangGraph, Pydantic AI, CrewAI, MS Agent
> Framework, OpenAI Agents SDK, Smolagents). Same metrics, same
> dataset, side-by-side trace. Best decision tool for "which one
> should we use".

> 6/ Phases 6–8 add HITL interrupts, MCP servers, and a
> deployment stack (FastAPI + Streamlit + HF + Docker Compose +
> Next.js streaming). All offline-reproducible in CI.

> 7/ Two production-grade deep-dive repos build on the hub:
> production-rag-pipeline and multi-agent-research-system.

> 8/ Free, MIT, contributions welcome. Skills matrix in the README
> is the fastest way to find what's interesting to you.
> <https://github.com/your-handle/agentic-ai-engineering>

## Phase C — Communities to post to (in order)

1. **Show HN** — Tuesday or Wednesday, 8–10 am Pacific.
2. **r/MachineLearning** — `[P]` tag. Same body as HN, slightly
   shorter.
3. **r/LangChain**, **r/LocalLLaMA** — emphasise the framework
   comparison + the HNSW deep-dive respectively.
4. **LangChain Discord** → `#share-your-work`.
5. **LlamaIndex Discord** → `#showcase`.
6. **Anthropic Discord** → `#share-your-projects` (MCP angle).
7. **Awesome-LLM PRs:**
   - [Hannibal046/Awesome-LLM](https://github.com/Hannibal046/Awesome-LLM)
   - [steven2358/awesome-generative-ai](https://github.com/steven2358/awesome-generative-ai)
   - [e2b-dev/awesome-ai-agents](https://github.com/e2b-dev/awesome-ai-agents)
   - [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers)
     (mention `06-mcp/`)
   - [aishwaryanr/awesome-generative-ai-guide](https://github.com/aishwaryanr/awesome-generative-ai-guide)
8. **Newsletters:** TLDR AI submissions inbox, AlphaSignal submissions,
   Ben's Bites tips inbox.
9. **Your network:** 5–10 personalised DMs to people whose work the
   repo cites or whose feedback you value most. (This is the highest-
   ROI step; the public posts amplify.)

## Phase D — After launch (first 72 hours)

- [ ] Triage every issue and PR within 24 h. The first issue you fail
  to respond to becomes the impression.
- [ ] Star count is a vanity metric; **issue thoughtfulness is not.**
  Promote the best questions into the README FAQ.
- [ ] Capture the launch traffic in your README — a "**Press / mentions**"
  section with links to threads that took off.
- [ ] Open a follow-up issue: "What should Phase 11.5 be?" Crowdsource
  the next direction.

## Phase E — The deep-dive cross-link (manual)

In each of:

- `production-rag-pipeline/README.md`
- `multi-agent-research-system/README.md`

add a top-of-README block:

> **Built on patterns from
> [agentic-ai-engineering](https://github.com/your-handle/agentic-ai-engineering).**
> See the [framework comparison deep-dive](https://github.com/your-handle/agentic-ai-engineering/blob/main/docs/deep-dives/04-framework-comparison.md)
> and the [MCP deep-dive](https://github.com/your-handle/agentic-ai-engineering/blob/main/docs/deep-dives/05-mcp.md)
> for the architectural rationale behind the choices in this repo.

That single block is the highest-bandwidth signal that the three
repos form a coherent body of work.
