# 05 — Evals & observability

Measurement is what separates a demo from a system. This folder covers both RAG-specific and agent-specific evaluation, plus self-hosted observability.

## Planned leaves

| Leaf | Topic | Status |
|---|---|---|
| `00-ragas-rag-eval/` | Faithfulness, Context Precision/Recall, Answer Relevancy — implemented on top of the shared LLM shim | ✅ Phase 4 |
| `01-ragas-agent-eval/` | Tool-call accuracy, agent goal accuracy, topic adherence on a committed 5-trace fixture | ✅ Phase 4 |
| `02-langfuse-tracing/` | Span+score recorder with the same shape as `langfuse.Langfuse`; swap-in real client in one line | ✅ Phase 4 |
| `03-llm-as-judge/` | Rubric, pairwise, and position-swap mitigated judges; tracks position-bias delta | ✅ Phase 4 |
| `04-synthetic-eval-data/` | Doc → Q&A generation with three filters; calibrates against the golden set | ✅ Phase 4 |
| `05-regression-suite/` | `regression.py` library + pytest fixture + opt-in `baseline.json` per leaf | ✅ Phase 4 |
| `06-cost-and-latency-bench/` | tiktoken-based token accounting + static price table; pareto labelling per model | ✅ Phase 4 |

