# All leaves

Every leaf of the hub repo, rendered in-browser. The notebooks are rendered statically by mkdocs-jupyter; to **execute** them in your browser, use the [JupyterLite site](../browser-execution.md).

## [Phase 0 — Foundations](00-foundations/index.md)

- [`01-structured-outputs`](00-foundations/01-structured-outputs/index.md) — _no headline metric_
- [`02-function-calling`](00-foundations/02-function-calling/index.md) — _no headline metric_
- [`03-streaming-patterns`](00-foundations/03-streaming-patterns/index.md) — _no headline metric_
- [`04-prompt-patterns`](00-foundations/04-prompt-patterns/index.md) — _no headline metric_

## [Phase 1 — RAG](01-rag/index.md)

- [`00-naive-rag`](01-rag/00-naive-rag/index.md) — `context_recall`=0.75 · `answer_exact_match_direct`=0.955
- [`01-chunking-strategies`](01-rag/01-chunking-strategies/index.md) — _no headline metric_
- [`02-embedding-comparison`](01-rag/02-embedding-comparison/index.md) — _no headline metric_
- [`03-hybrid-search`](01-rag/03-hybrid-search/index.md) — _no headline metric_
- [`04-reranking`](01-rag/04-reranking/index.md) — _no headline metric_
- [`05-query-transformation`](01-rag/05-query-transformation/index.md) — _no headline metric_
- [`06-self-rag`](01-rag/06-self-rag/index.md) — _no headline metric_
- [`07-corrective-rag`](01-rag/07-corrective-rag/index.md) — _no headline metric_
- [`08-agentic-rag`](01-rag/08-agentic-rag/index.md) — _no headline metric_
- [`09-graph-rag`](01-rag/09-graph-rag/index.md) — _no headline metric_
- [`10-multimodal-rag`](01-rag/10-multimodal-rag/index.md) — _no headline metric_
- [`11-long-context-rag`](01-rag/11-long-context-rag/index.md) — _no headline metric_
- [`12-comparison-bench`](01-rag/12-comparison-bench/index.md) — _no headline metric_

## [Phase 2 — Indexing internals](02-indexing/index.md)

- [`00-vector-db-comparison`](02-indexing/00-vector-db-comparison/index.md) — _no headline metric_
- [`01-hnsw-deep-dive`](02-indexing/01-hnsw-deep-dive/index.md) — _no headline metric_
- [`02-ivf-pq-quantization`](02-indexing/02-ivf-pq-quantization/index.md) — _no headline metric_
- [`03-bm25-and-hybrid`](02-indexing/03-bm25-and-hybrid/index.md) — _no headline metric_
- [`04-knowledge-graph-index`](02-indexing/04-knowledge-graph-index/index.md) — _no headline metric_
- [`05-summary-tree-index`](02-indexing/05-summary-tree-index/index.md) — _no headline metric_
- [`06-colbert-late-interaction`](02-indexing/06-colbert-late-interaction/index.md) — _no headline metric_
- [`07-incremental-indexing`](02-indexing/07-incremental-indexing/index.md) — _no headline metric_

## [Phase 3 — Agentic frameworks](03-agentic-frameworks/index.md)

- [`00-react-from-scratch`](03-agentic-frameworks/00-react-from-scratch/index.md) — `tool_call_accuracy`=1 · `final_answer_grounded`=0.333
- [`01-langgraph`](03-agentic-frameworks/01-langgraph/index.md) — `tool_call_accuracy`=1 · `final_answer_grounded`=0.333
- [`02-pydantic-ai`](03-agentic-frameworks/02-pydantic-ai/index.md) — `tool_call_accuracy`=1 · `final_answer_grounded`=0.333
- [`03-crewai`](03-agentic-frameworks/03-crewai/index.md) — `tool_call_accuracy`=1 · `final_answer_grounded`=0.333
- [`04-microsoft-agent-framework`](03-agentic-frameworks/04-microsoft-agent-framework/index.md) — `tool_call_accuracy`=1 · `final_answer_grounded`=0.333
- [`05-openai-agents-sdk`](03-agentic-frameworks/05-openai-agents-sdk/index.md) — `tool_call_accuracy`=1 · `final_answer_grounded`=0.333
- [`06-smolagents`](03-agentic-frameworks/06-smolagents/index.md) — `tool_call_accuracy`=1 · `final_answer_grounded`=0.333
- [`07-framework-comparison`](03-agentic-frameworks/07-framework-comparison/index.md) — `tool_call_accuracy`=1 · `final_answer_grounded`=0.333

## [Phase 4 — Human-in-the-loop](04-human-in-the-loop/index.md)

- [`00-interrupt-and-resume`](04-human-in-the-loop/00-interrupt-and-resume/index.md) — _no headline metric_
- [`01-approval-gates`](04-human-in-the-loop/01-approval-gates/index.md) — _no headline metric_
- [`02-edit-state`](04-human-in-the-loop/02-edit-state/index.md) — _no headline metric_
- [`03-time-travel-debug`](04-human-in-the-loop/03-time-travel-debug/index.md) — _no headline metric_
- [`04-streaming-with-intervention`](04-human-in-the-loop/04-streaming-with-intervention/index.md) — _no headline metric_
- [`05-async-hitl-via-queue`](04-human-in-the-loop/05-async-hitl-via-queue/index.md) — _no headline metric_

## [Phase 5 — Evals & observability](05-evals-and-observability/index.md)

- [`00-ragas-rag-eval`](05-evals-and-observability/00-ragas-rag-eval/index.md) — `context_recall`=0.827 · `faithfulness`=1
- [`01-ragas-agent-eval`](05-evals-and-observability/01-ragas-agent-eval/index.md) — `tool_call_accuracy`=0.8
- [`02-langfuse-tracing`](05-evals-and-observability/02-langfuse-tracing/index.md) — _no headline metric_
- [`03-llm-as-judge`](05-evals-and-observability/03-llm-as-judge/index.md) — _no headline metric_
- [`04-synthetic-eval-data`](05-evals-and-observability/04-synthetic-eval-data/index.md) — _no headline metric_
- [`05-regression-suite`](05-evals-and-observability/05-regression-suite/index.md) — _no headline metric_
- [`06-cost-and-latency-bench`](05-evals-and-observability/06-cost-and-latency-bench/index.md) — _no headline metric_

## [Phase 6 — MCP](06-mcp/index.md)

- [`00-mcp-server-basics`](06-mcp/00-mcp-server-basics/index.md) — `canonical_method_coverage`=1 · `schema_validity_rate`=1
- [`01-mcp-client-in-agent`](06-mcp/01-mcp-client-in-agent/index.md) — `tool_call_accuracy`=1 · `final_answer_grounded`=0.333
- [`02-mcp-with-resources`](06-mcp/02-mcp-with-resources/index.md) — _no headline metric_
- [`03-custom-mcp-for-internal-api`](06-mcp/03-custom-mcp-for-internal-api/index.md) — _no headline metric_

## [Phase 7 — Deployment](07-deployment-patterns/index.md)

- [`00-fastapi-streaming-agent`](07-deployment-patterns/00-fastapi-streaming-agent/index.md) — _no headline metric_
- [`01-streamlit-demo-template`](07-deployment-patterns/01-streamlit-demo-template/index.md) — _no headline metric_
- [`02-docker-compose-stack`](07-deployment-patterns/02-docker-compose-stack/index.md) — _no headline metric_
- [`03-hf-spaces-deploy`](07-deployment-patterns/03-hf-spaces-deploy/index.md) — _no headline metric_
- [`04-ts-vercel-ai-sdk-chat`](07-deployment-patterns/04-ts-vercel-ai-sdk-chat/index.md) — _no headline metric_
