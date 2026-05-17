# 03 — Agentic frameworks

Same task implemented across 6 frameworks plus a from-scratch ReAct. Comparison matrix in the last leaf.

## Planned leaves

| Leaf | Framework | Status |
|---|---|---|
| `00-react-from-scratch/` | Pure-Python ReAct loop with parse-then-dispatch — proves fundamentals | ✅ Phase 5 |
| `01-langgraph/` | `StateGraph` + supervisor pattern + checkpointer; foundation for the HITL phase | ✅ Phase 5 |
| `02-pydantic-ai/` | `Agent[Deps, Output]` with typed dependencies and structured output | ✅ Phase 5 |
| `03-crewai/` | `Agent` + `Task` + `Crew` (sequential / hierarchical); role/goal/backstory | ✅ Phase 5 |
| `04-microsoft-agent-framework/` | Sequential / concurrent / group-chat workflows | ✅ Phase 5 |
| `05-openai-agents-sdk/` | `Agent` + `Runner` + handoffs / guardrails / sessions | ✅ Phase 5 |
| `06-smolagents/` | `CodeAgent` — code as the action, sandbox runs Python | ✅ Phase 5 |
| `07-framework-comparison/` | Aggregated leaderboard + capability matrix + pick-when guide | ✅ Phase 5 |

**Shared task:** Research and summarize a given arxiv paper with citations — implemented in `task.py` as `search_corpus / fetch_paper / cite` tools over the canonical corpus.

