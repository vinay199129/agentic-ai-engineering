# Built from scratch — what the hub re-implements

A common (fair) criticism of agent-portfolio repos: *"You wired up
LangChain and copied a tutorial."* This repo answers that head-on by
re-implementing the **load-bearing infrastructure** in pure Python so
the abstractions are legible and so CI never needs an API key.

This page is the inventory. Each entry lists the file, line count
(everything below is honest LOC, not marketing), what library it
replaces, and what understanding it gives you.

---

## 1. `shared/llm.py` — provider-agnostic LLM shim with deterministic cache

- **File:** [`shared/llm.py`](https://github.com/vinay199129/agentic-ai-engineering/tree/main/shared/) — **276 lines**
- **Replaces:** parts of `litellm`, the OpenAI/Anthropic SDKs' typed
  surface, and any "LLM cache" middleware (`langchain.cache`,
  `gptcache`, etc.).
- **What it does:**
  - One `complete()` entry point that accepts messages + tools,
    normalises the response into a typed `Completion`, and falls back
    through providers when keys are missing.
  - A JSONL on-disk cache keyed by `stable_key(prompt, model,
    tool_set, temperature)`. When `LLM_CACHE_ONLY=1` (the CI flag) the
    shim refuses to make a network call — if the key isn't cached, it
    raises. This is why CI is fully reproducible without secrets.
  - A symmetric `embed()` for embeddings with the same cache contract.
- **Why from scratch:** so every notebook in the hub runs offline in
  CI against committed cache files, and so switching providers is a
  one-line change instead of a refactor.

## 2. `06-mcp/mcp_core.py` — in-process JSON-RPC 2.0 MCP server + client

- **File:** [`06-mcp/mcp_core.py`](leaves/06-mcp/index.md) — **579 lines**
- **Replaces:** the official `mcp` Python SDK + a transport layer
  (stdio / SSE / WebSocket).
- **What it does:**
  - JSON-RPC 2.0 wire protocol (request, notification, error codes,
    batched requests) — built on stdlib `json` only.
  - `Server` with first-class **tools / resources / prompts** primitives,
    full method coverage of the canonical MCP spec (`initialize`,
    `tools/list`, `tools/call`, `resources/list`, `resources/read`,
    `prompts/list`, `prompts/get`), and an audit log used by the snapshots.
  - `Client` connected via an in-process `Transport` — no socket, no
    subprocess, runs inside a notebook cell.
  - `build_corpus_server(...)` factory + a deterministic
    `mcp_agent_solve(client, question)` loop so MCP traces are directly
    comparable to native-tool traces from Phase 5.
- **Why from scratch:** the official SDK ties you to a transport and to
  Python 3.11+; teaching MCP is about making the *protocol* visible,
  not the SDK ergonomics. The leaves can ship to JupyterLite because
  `mcp_core` imports nothing outside stdlib + the hub's embedder.

## 3. `04-human-in-the-loop/hitl.py` — mini-LangGraph with interrupts

- **File:** [`04-human-in-the-loop/hitl.py`](leaves/04-human-in-the-loop/index.md) — **577 lines**
- **Replaces:** `langgraph` + `langgraph-checkpoint` (the subset needed
  for HITL patterns).
- **What it does:**
  - `Graph` — typed nodes, edges, conditional edges, terminal nodes.
  - `Checkpointer` with `put` / `get` / **`fork`** (time-travel
    debugging in 30 lines).
  - `Interrupt` exception + `Command(resume=…)` reply object — exactly
    the surface LangGraph exposes for interrupt/resume.
  - `stream_events()` — yields `node_complete`, `interrupt`, `done`
    frames suitable for SSE.
  - `build_research_graph()` and `run_scenario()` — a ready-made
    planner → search → draft → publish flow used by every Phase 6 leaf.
- **Why from scratch:** the six HITL leaves all need the same primitive
  surface but LangGraph's actual implementation is too sprawling to read
  during a teaching session. 577 lines is the minimum honest implementation
  of interrupt/resume + time-travel + streaming + tool-call approval.

## 4. `03-agentic-frameworks/00-react-from-scratch/` + `task.py`

- **Files:**
  [`task.py`](leaves/03-agentic-frameworks/index.md) — **368 lines** ·
  [`00-react-from-scratch/eval.py`](leaves/03-agentic-frameworks/00-react-from-scratch/index.md) — **141 lines**
- **Replaces:** the ReAct loop you'd otherwise import from
  `langchain.agents` / `llama_index.agent` / `smolagents`.
- **What it does:**
  - `task.py` exports the shared `search_corpus` / `fetch_paper` /
    `cite` tools and a `run_evaluation` harness used by all 8 framework
    leaves. The exact same tool surface is fed to LangGraph, Pydantic AI,
    CrewAI, MS Agent Framework, OpenAI Agents SDK, and Smolagents so
    the comparison is apples-to-apples.
  - `00-react-from-scratch/eval.py` is a complete ReAct
    think-act-observe loop in 141 lines. No framework. Reads exactly like
    the original paper.

## 5. The indexing stack — HNSW, IVF-PQ, BM25, ColBERT, KG, summary-tree

| Leaf | LOC | What it implements from scratch | Replaces |
|---|---:|---|---|
| [`02-indexing/00-vector-db-comparison`](leaves/02-indexing/00-vector-db-comparison/index.md) | 242 | Flat / HNSW / IVF / PQ / MaxSim side-by-side in NumPy | FAISS, Qdrant, Chroma, pgvector benchmarks |
| [`02-indexing/01-hnsw-deep-dive`](leaves/02-indexing/01-hnsw-deep-dive/index.md) | 184 | Multi-layer proximity graph + greedy beam search | `hnswlib` |
| [`02-indexing/02-ivf-pq-quantization`](leaves/02-indexing/02-ivf-pq-quantization/index.md) | 150 | k-means coarse quantiser + product-quantiser codebooks | FAISS `IndexIVFPQ` |
| [`02-indexing/03-bm25-and-hybrid`](leaves/02-indexing/03-bm25-and-hybrid/index.md) | 136 | BM25 scoring + RRF fusion | `rank_bm25`, ElasticSearch BM25 |
| [`02-indexing/06-colbert-late-interaction`](leaves/02-indexing/06-colbert-late-interaction/index.md) | 117 | MaxSim late-interaction scoring | `colbert-ai` |
| [`02-indexing/07-incremental-indexing`](leaves/02-indexing/07-incremental-indexing/index.md) | 173 | Add / delete / tombstone / rebuild lifecycle on a flat index | every vector DB's "incremental" docs |

**Why from scratch:** the indexing leaves are where the field is most
"magic library calls." Re-implementing each algorithm in 100–250
lines of NumPy makes the tradeoffs (recall vs. ef, M vs. RAM, nlist
vs. nprobe, BM25 k1/b) explicit instead of opaque.

## 6. The evals stack — RAGAS-style, judge, regression, cost/latency

| Leaf | LOC | What it implements from scratch | Replaces |
|---|---:|---|---|
| [`05-evals-and-observability/00-ragas-rag-eval`](leaves/05-evals-and-observability/00-ragas-rag-eval/index.md) | 230 | `faithfulness`, `answer_relevancy`, `context_precision`, `context_recall` | `ragas` |
| [`05-evals-and-observability/01-ragas-agent-eval`](leaves/05-evals-and-observability/01-ragas-agent-eval/index.md) | 173 | Agent-trace metrics: tool-call accuracy, step efficiency, goal completion | `ragas.metrics.agents` |
| [`05-evals-and-observability/03-llm-as-judge`](leaves/05-evals-and-observability/03-llm-as-judge/index.md) | 169 | Rubric judge + pairwise judge + position-bias mitigation | `langchain.evaluation`, `mt-bench` |
| [`05-evals-and-observability/04-synthetic-eval-data`](leaves/05-evals-and-observability/04-synthetic-eval-data/index.md) | 189 | Multi-difficulty Q&A generation with grounding checks | `ragas.testset` |
| [`05-evals-and-observability/05-regression-suite/regression.py`](leaves/05-evals-and-observability/05-regression-suite/index.md) | 120 | Snapshot diffing + > 5% regression gate | `evidently`, `deepchecks` |
| [`05-evals-and-observability/06-cost-and-latency-bench`](leaves/05-evals-and-observability/06-cost-and-latency-bench/index.md) | 150 | Token + wall-clock benchmark harness | hand-rolled spreadsheet |

**Why from scratch:** `ragas` is a great library but it (a) takes API
keys to compute most metrics and (b) hides the prompt and the math.
Re-implementing each metric makes the "what is faithfulness actually
measuring?" conversation possible, and the regression gate keeps the
hub honest.

---

## Total

Roughly **4 200 lines of from-scratch implementation code** — not
counting leaf notebooks, eval harnesses, READMEs, or tests. Every line
is pedagogically motivated: if a library would have hidden the
mechanic the leaf is teaching, we rebuilt the mechanic.

## What we deliberately *did not* re-implement

We use real libraries where understanding the internals is not the
point:

- **Postgres + pgvector** for the deployment stack — operating a DB
  is its own discipline.
- **FastAPI / Starlette** for HTTP — re-implementing SSE/JSON streaming
  is uninteresting.
- **Next.js + Vercel AI SDK** in the TypeScript leaf — same reason.
- **Docker Compose** in the deployment leaf — composing services is
  the point; reinventing it is not.
- **`langgraph`, `pydantic-ai`, `crewai`, `agent-framework`,
  `openai-agents`, `smolagents`** in their *own* framework leaves —
  the point of those leaves is to show idiomatic usage. The
  `00-react-from-scratch` leaf gives you the from-scratch comparison.

That delineation is the actual editorial line of this repo:
**re-implement when the implementation is the lesson, integrate when
the integration is the lesson.**
