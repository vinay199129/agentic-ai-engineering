# Agentic-frameworks leaderboard

## Metrics (same canonical task)

| framework | tool_call_accuracy | final_answer_grounded | avg_n_steps | avg_latency_ms |
| --- | --- | --- | --- | --- |
| `react-from-scratch` | 1.0000 | 0.3333 | 4.0000 | 0.8940 |
| `langgraph` | 1.0000 | 0.3333 | 4.0000 | 1.2610 |
| `pydantic-ai` | 1.0000 | 0.3333 | 4.0000 | 0.7460 |
| `crewai` | 1.0000 | 0.3333 | 4.0000 | 0.7750 |
| `microsoft-agent-framework` | 1.0000 | 0.3333 | 4.0000 | 0.7640 |
| `openai-agents-sdk` | 1.0000 | 0.3333 | 4.0000 | 0.7470 |
| `smolagents` | 1.0000 | 0.3333 | 4.0000 | 0.9790 |

## Capability matrix

| framework | typed_io | graph_state | conditional_routing | streaming | checkpointer | code_action | handoffs | vendor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `react-from-scratch` | - | - | - | - | - | - | - | self |
| `langgraph` | ~ | + | + | + | + | - | ~ | LangChain |
| `pydantic-ai` | + | - | ~ | + | - | - | - | Pydantic |
| `crewai` | ~ | - | ~ | ~ | - | - | ~ | CrewAI |
| `microsoft-agent-framework` | ~ | + | + | + | + | - | + | Microsoft |
| `openai-agents-sdk` | ~ | - | + | + | ~ | - | + | OpenAI |
| `smolagents` | ~ | - | ~ | + | - | + | - | HuggingFace |

*+ = first-class; ~ = partial / convention; - = absent*

## Pick this framework when…

* **`react-from-scratch`** — you're teaching, debugging, or building a one-off.
* **`langgraph`** — you need branchy multi-agent topologies + checkpoint-based HITL.
* **`pydantic-ai`** — you want type-safe, structured-output agents in a typed Python codebase.
* **`crewai`** — the task decomposes into named roles you can describe to a stakeholder.
* **`microsoft-agent-framework`** — you're inside the Microsoft / Semantic Kernel ecosystem and want production-grade multi-agent workflows.
* **`openai-agents-sdk`** — you're on the OpenAI stack and want the smallest possible production API.
* **`smolagents`** — your reasoning benefits from code as the action (math, compositional steps, data wrangling).
