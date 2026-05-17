# Skills matrix

Mapping topic folders → claimed competencies. **Phases 0–8 ship — every
leaf below has a runnable notebook, `eval.py`, and a committed
`eval-snapshot.json` that CI compares against `main`.**

| Skill | Where to see it | Status |
|---|---|---|
| Structured outputs (Pydantic, JSON-mode) | `00-foundations/01-structured-outputs/` | ✅ shipped |
| Function / tool calling | `00-foundations/02-function-calling/` | ✅ shipped |
| Streaming patterns (SSE, async gen) | `00-foundations/03-streaming-patterns/` | ✅ shipped |
| Anthropic workflow patterns (chain, route, parallel, orchestrator, evaluator) | `00-foundations/04-prompt-patterns/` | ✅ shipped |
| Naive RAG baseline | `01-rag/00-naive-rag/` | ✅ shipped |
| Chunking strategies (5 variants) | `01-rag/01-chunking-strategies/` | ✅ shipped |
| Embedding-model selection | `01-rag/02-embedding-comparison/` | ✅ shipped |
| Hybrid retrieval (BM25 + dense + RRF) | `01-rag/03-hybrid-search/` | ✅ shipped |
| Reranking (Cohere, BGE, ColBERT) | `01-rag/04-reranking/` | ✅ shipped |
| Query transformation (HyDE, multi-query, step-back) | `01-rag/05-query-transformation/` | ✅ shipped |
| Self-RAG | `01-rag/06-self-rag/` | ✅ shipped |
| Corrective RAG (CRAG) | `01-rag/07-corrective-rag/` | ✅ shipped |
| Agentic RAG | `01-rag/08-agentic-rag/` | ✅ shipped |
| GraphRAG | `01-rag/09-graph-rag/` | ✅ shipped |
| Multimodal RAG (ColPali / Voyage Multimodal) | `01-rag/10-multimodal-rag/` | ✅ shipped |
| Long-context / contextual retrieval | `01-rag/11-long-context-rag/` | ✅ shipped |
| Cross-technique benchmarking | `01-rag/12-comparison-bench/` | ✅ shipped |
| Vector-DB selection & benchmarking | `02-indexing/00-vector-db-comparison/` | ✅ shipped |
| HNSW internals | `02-indexing/01-hnsw-deep-dive/` | ✅ shipped |
| IVF-PQ quantization | `02-indexing/02-ivf-pq-quantization/` | ✅ shipped |
| BM25 internals + hybrid fusion | `02-indexing/03-bm25-and-hybrid/` | ✅ shipped |
| Knowledge-graph indexing | `02-indexing/04-knowledge-graph-index/` | ✅ shipped |
| Summary-tree / hierarchical indexing | `02-indexing/05-summary-tree-index/` | ✅ shipped |
| ColBERT late interaction | `02-indexing/06-colbert-late-interaction/` | ✅ shipped |
| Incremental indexing (deltas, deletes) | `02-indexing/07-incremental-indexing/` | ✅ shipped |
| ReAct from scratch | `03-agentic-frameworks/00-react-from-scratch/` | ✅ shipped |
| LangGraph (stateful, checkpointer, subgraphs) | `03-agentic-frameworks/01-langgraph/` | ✅ shipped |
| Pydantic AI (type-safe) | `03-agentic-frameworks/02-pydantic-ai/` | ✅ shipped |
| CrewAI (roles, hierarchical crews) | `03-agentic-frameworks/03-crewai/` | ✅ shipped |
| Microsoft Agent Framework | `03-agentic-frameworks/04-microsoft-agent-framework/` | ✅ shipped |
| OpenAI Agents SDK (handoffs, guardrails) | `03-agentic-frameworks/05-openai-agents-sdk/` | ✅ shipped |
| Smolagents (code-as-action) | `03-agentic-frameworks/06-smolagents/` | ✅ shipped |
| Framework tradeoff analysis | `03-agentic-frameworks/07-framework-comparison/` | ✅ shipped |
| HITL interrupt/resume | `04-human-in-the-loop/00-interrupt-and-resume/` | ✅ shipped |
| Tool-call approval gates | `04-human-in-the-loop/01-approval-gates/` | ✅ shipped |
| Edit state mid-run | `04-human-in-the-loop/02-edit-state/` | ✅ shipped |
| Time-travel debugging | `04-human-in-the-loop/03-time-travel-debug/` | ✅ shipped |
| Streaming with mid-run intervention | `04-human-in-the-loop/04-streaming-with-intervention/` | ✅ shipped |
| Async HITL via queue (Slack/email webhook) | `04-human-in-the-loop/05-async-hitl-via-queue/` | ✅ shipped |
| RAGAS RAG metrics | `05-evals-and-observability/00-ragas-rag-eval/` | ✅ shipped |
| RAGAS agent metrics | `05-evals-and-observability/01-ragas-agent-eval/` | ✅ shipped |
| Langfuse tracing (self-hosted) | `05-evals-and-observability/02-langfuse-tracing/` | ✅ shipped |
| LLM-as-judge (rubric, pairwise, bias mitigation) | `05-evals-and-observability/03-llm-as-judge/` | ✅ shipped |
| Synthetic eval-data generation | `05-evals-and-observability/04-synthetic-eval-data/` | ✅ shipped |
| Eval regression in CI | `05-evals-and-observability/05-regression-suite/` | ✅ shipped |
| Cost & latency benchmarking | `05-evals-and-observability/06-cost-and-latency-bench/` | ✅ shipped |
| MCP server (in-process JSON-RPC 2.0) | `06-mcp/00-mcp-server-basics/` | ✅ shipped |
| MCP client in an agent | `06-mcp/01-mcp-client-in-agent/` | ✅ shipped |
| MCP resources + prompts | `06-mcp/02-mcp-with-resources/` | ✅ shipped |
| Custom MCP wrapping a real API | `06-mcp/03-custom-mcp-for-internal-api/` | ✅ shipped |
| FastAPI streaming agent (SSE) | `07-deployment-patterns/00-fastapi-streaming-agent/` | ✅ shipped |
| Streamlit demo template | `07-deployment-patterns/01-streamlit-demo-template/` | ✅ shipped |
| Docker Compose full stack | `07-deployment-patterns/02-docker-compose-stack/` | ✅ shipped |
| HF Spaces CI deploy | `07-deployment-patterns/03-hf-spaces-deploy/` | ✅ shipped |
| TypeScript / Vercel AI SDK chat | `07-deployment-patterns/04-ts-vercel-ai-sdk-chat/` | ✅ shipped |

Legend: ✅ shipped · 🚧 in progress · ⏳ pending
