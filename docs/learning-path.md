# Learning path

A recommended traversal order. Each step builds on the previous one; skip ahead at your own peril.

## 1. Foundations *(half a day)*

- `00-foundations/01-structured-outputs/` — Pydantic for tool schemas
- `00-foundations/02-function-calling/` — native vs JSON-schema vs Pydantic AI
- `00-foundations/03-streaming-patterns/` — SSE, async generators, partial JSON
- `00-foundations/04-prompt-patterns/` — the 5 Anthropic workflow patterns

## 2. RAG baseline *(half a day)*

- `01-rag/00-naive-rag/` — chunk → embed → top-k → stuff
- `01-rag/01-chunking-strategies/` — fixed, recursive, semantic, propositional, contextual
- `01-rag/02-embedding-comparison/` — OpenAI vs Cohere vs Voyage vs BGE

## 3. Learn to measure *(do this BEFORE going deeper)*

- `05-evals-and-observability/00-ragas-rag-eval/`
- `05-evals-and-observability/04-synthetic-eval-data/`

## 4. Advanced RAG *(1–2 days)*

- `01-rag/03-hybrid-search/` → `01-rag/12-comparison-bench/`

## 5. Indexing internals *(1 day)*

- `02-indexing/00-vector-db-comparison/` → `02-indexing/07-incremental-indexing/`

## 6. Agents *(2–3 days)*

- `03-agentic-frameworks/00-react-from-scratch/` — build it before using a framework
- `03-agentic-frameworks/01-langgraph/`
- Pick 1–2 others to compare
- `03-agentic-frameworks/07-framework-comparison/`

## 7. Production agents

- `04-human-in-the-loop/` — interrupt/resume, approval gates, time-travel
- `06-mcp/` — modern tool integration

## 8. Ship it

- `07-deployment-patterns/` — FastAPI streaming, Streamlit template, Docker compose, HF Spaces

## 9. Deep-dives *(study the production repos)*

- `production-rag-pipeline` — see how it all comes together
- `multi-agent-research-system` — HITL + multi-agent + MCP in production form
