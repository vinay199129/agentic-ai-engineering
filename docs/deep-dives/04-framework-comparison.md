# Framework comparison — the same agent, six different ways

> Source leaves: [`03-agentic-frameworks/`](../leaves/03-agentic-frameworks/index.md)
> (00 ReAct from scratch + 01–06 framework leaves + 07 comparison).

## Why we built this

Agent frameworks proliferate. Twitter says you must use LangGraph this
quarter; the Anthropic blog says use nothing; a recruiter only knows
the name CrewAI. The hub answers the question by building **the same
task** seven times and measuring the same metrics on each.

The task: *"Given an arxiv paper ID, search the corpus for it, fetch
its abstract, and return a one-paragraph summary with at least one
citation."* Boring. Deliberately. Boring tasks expose the framework's
*ergonomics*, not the framework's marketing.

## The implementations at a glance

| # | Framework | Lines (incl. boilerplate) | Mental model |
|---|---|---:|---|
| 00 | ReAct from scratch | ~120 | Hand-rolled think-act-observe loop |
| 01 | LangGraph | ~150 | Typed state graph with a checkpointer |
| 02 | Pydantic AI | ~80 | Type-safe agent + structured dependencies |
| 03 | CrewAI | ~110 | Roles + tasks + crew orchestration |
| 04 | MS Agent Framework | ~140 | Sequential / concurrent / group-chat workflows |
| 05 | OpenAI Agents SDK | ~95 | Handoffs + guardrails + sessions |
| 06 | Smolagents | ~70 | Code-as-action — the agent writes Python |
| 07 | Comparison | — | Side-by-side trace + opinionated commentary |

Line counts include imports and the offline-fallback solver in each
leaf's `eval.py` — they are honest about what you actually have to write.

## What the snapshots actually measure

Each leaf emits the same metrics so they're directly comparable:

* `final_answer_correct` (judged offline against expected sources)
* `tool_call_accuracy` (did the agent call the right tools?)
* `avg_n_steps` (proxy for token cost)
* `avg_latency_ms`

A condensed view (numbers vary run to run; consult the live snapshots):

| # | Framework | answer correct | tool acc | steps | latency |
|---|---|---:|---:|---:|---:|
| 00 | ReAct from scratch | 1.00 | 1.00 | 4.0 | 1 ms |
| 01 | LangGraph | 1.00 | 1.00 | 4.0 | 2 ms |
| 02 | Pydantic AI | 1.00 | 1.00 | 4.0 | 1 ms |
| 03 | CrewAI | 1.00 | 0.95 | 5.5 | 3 ms |
| 04 | MS Agent Framework | 1.00 | 1.00 | 4.0 | 2 ms |
| 05 | OpenAI Agents SDK | 1.00 | 1.00 | 4.0 | 1 ms |
| 06 | Smolagents | 1.00 | 1.00 | 3.0 | 2 ms |

(All running on the offline solver in `task.py`. The point of the
numbers is that the *shape* of the differences — extra steps in CrewAI,
fewer in Smolagents — is reproducible; the absolute latencies are
microseconds because there is no real LLM round-trip.)

## What I'd actually pick, by problem shape

* **A graph with branches that need to resume across restarts** →
  **LangGraph**. The typed state + checkpointer combo is unmatched.
  Pair it with Phase 6's HITL patterns and you have an industrial agent.

* **A typed Python codebase that already lives in Pydantic models** →
  **Pydantic AI**. The integration is so clean it's barely a framework.

* **A crew of agents with distinct personas + hierarchical delegation** →
  **CrewAI**. The roles abstraction earns its keep. Avoid for
  single-agent tasks; the overhead shows.

* **"Code is the API" / dynamic data-wrangling** → **Smolagents**.
  Code-as-action makes complex tool composition tractable.

* **You are deeply inside the OpenAI ecosystem (Realtime, GPT-4o, image)** →
  **OpenAI Agents SDK**. Handoffs are first-class; guardrails are the
  cleanest in the field.

* **You're shipping inside the Microsoft 365 / Azure surface** →
  **MS Agent Framework**. The sequential / concurrent / group-chat
  workflows match Azure's deployment story.

* **You want to *understand* what every framework is doing under the
  hood** → **ReAct from scratch**, every time, before anything else.

## What the leaderboard does not capture

* **DX during failure.** All seven frameworks complete the happy
  path. Three become difficult to debug when the LLM emits a malformed
  tool call. (Trace through CrewAI and MS-AF and you'll see what I
  mean.)
* **Upgrade pain.** LangGraph and OpenAI Agents SDK have shipped
  breaking changes ~every quarter. Pydantic AI has been stable. Bake
  the upgrade cost into your decision.
* **Community vs. company momentum.** CrewAI and Smolagents are
  community-first; OpenAI / Microsoft / LangChain ship on roadmaps.
  Choose the support mode you can absorb.

## How to use this leaf as a forcing function

Whenever someone on the team says *"we should switch to X"*, fork the
relevant leaf, reimplement the task, run the eval, and look at the
delta. Five hours of work; eliminates a quarter of churn.

## References

- [LangGraph docs](https://langchain-ai.github.io/langgraph/)
- [Pydantic AI docs](https://ai.pydantic.dev/)
- [Anthropic — Building effective agents](https://www.anthropic.com/research/building-effective-agents)
