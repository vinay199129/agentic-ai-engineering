# Realistic use cases — what each leaf maps to in production

The hub uses an arXiv `cs.CL` corpus as its canonical dataset because
it is freely redistributable, factually rich, and legible to a
technical audience (see [ADR 0006](architecture-decisions/0006-arxiv-corpus-choice.md)).
But every pattern in the hub is a stand-in for a real production
problem. This page draws the mapping explicitly so reviewers and
future-you can see the leaves as solutions to problems they recognise.

The format: **problem you'll meet in production → which leaf to copy
→ what to change.**

---

## Customer support — "Why did my charge fail?"

> **Problem:** A SaaS support agent needs to answer billing /
> entitlement / dunning questions over a corpus of ~30 k internal
> KB articles + the last 90 days of ticket history. Wrong answers
> are escalations; hallucinated policy is a refund.

| Need | Leaf to start from | What to change |
|---|---|---|
| Baseline retrieval | [`01-rag/00-naive-rag`](leaves/01-rag/00-naive-rag/index.md) | Swap the loader for your KB; chunk on `\n## ` headings |
| Lift recall from 65% to 90% | [`01-rag/03-hybrid-search`](leaves/01-rag/03-hybrid-search/index.md) + [`01-rag/04-reranking`](leaves/01-rag/04-reranking/index.md) | BM25 on ticket IDs + dense on prose; reranker on top-50 → top-5 |
| Faithfulness ("did the answer follow policy?") | [`05-evals-and-observability/00-ragas-rag-eval`](leaves/05-evals-and-observability/00-ragas-rag-eval/index.md) | Replace the cs.CL golden Q&A with 200 real tickets + the approved responses |
| Block hallucinated refunds | [`01-rag/07-corrective-rag`](leaves/01-rag/07-corrective-rag/index.md) | Wire the "incorrect" bucket to "I don't know" instead of web search |
| Escalation HITL | [`04-human-in-the-loop/01-approval-gates`](leaves/04-human-in-the-loop/01-approval-gates/index.md) | Any refund > $X triggers the interrupt; resume sends to Slack-bot |

---

## Internal API agent — "Wrap an unfriendly enterprise API"

> **Problem:** Your finance team has a SOAP-era reporting API.
> The agent should answer "What was Q1 revenue by region?" without
> the user (or the LLM) ever seeing the raw 17-field response or the
> 6-key auth dance.

| Need | Leaf | What to change |
|---|---|---|
| Hide the API behind a clean tool surface | [`06-mcp/03-custom-mcp-for-internal-api`](leaves/06-mcp/03-custom-mcp-for-internal-api/index.md) | Replace the demo upstream with your SOAP / gRPC / REST client; reuse the `payload_trim_ratio` metric in the snapshot |
| Rate-limit the upstream | same leaf | The leaf's per-tool rate limiter is the production pattern, not a demo |
| Audit every tool call | [`06-mcp/00-mcp-server-basics`](leaves/06-mcp/00-mcp-server-basics/index.md) | The audit log on `Server` is the compliance record |
| Govern access to documents | [`06-mcp/02-mcp-with-resources`](leaves/06-mcp/02-mcp-with-resources/index.md) | Promote the docs/configs the agent may read into `resources/*` URIs with row-level filtering |

---

## Engineering knowledge agent — "Code-aware Q&A over our monorepo"

> **Problem:** New engineers ask the same 30 questions per quarter:
> *"How do we deploy?", "Where does X read its config from?",
> "What pattern do we use for retries?"*. We want an agent that
> answers from `docs/`, the runbooks, and inline code comments —
> with a citation per claim.

| Need | Leaf | What to change |
|---|---|---|
| Semantic + lexical retrieval over `.md` + code | [`02-indexing/03-bm25-and-hybrid`](leaves/02-indexing/03-bm25-and-hybrid/index.md) | Tokenise camelCase / snake_case; index path-suffixes as boost terms |
| Step-back / multi-query for vague questions | [`01-rag/05-query-transformation`](leaves/01-rag/05-query-transformation/index.md) | Step-back for "how do we deploy?"; multi-query for ambiguous ones |
| Cite the source file/line | [`01-rag/00-naive-rag`](leaves/01-rag/00-naive-rag/index.md) | Store `path:line` as metadata; render as a GitHub permalink |
| Re-index nightly without rebuilding | [`02-indexing/07-incremental-indexing`](leaves/02-indexing/07-incremental-indexing/index.md) | Detect changed files via `git diff`; tombstone old chunks; upsert new |

---

## Multi-document research — "Summarise the last 90 days of incidents"

> **Problem:** SREs ask "what kinds of postgres incidents have we had
> this quarter?" The answer is not in any one postmortem; it's a
> *synthesis* over hundreds.

| Need | Leaf | What to change |
|---|---|---|
| Global synthesis over many docs | [`01-rag/09-graph-rag`](leaves/01-rag/09-graph-rag/index.md) | Entities = services, error codes, components; relationships = "caused", "mitigated by" |
| Hierarchical TL;DR | [`02-indexing/05-summary-tree-index`](leaves/02-indexing/05-summary-tree-index/index.md) | Roll up incident docs → weekly summaries → quarterly summaries |
| Planner → researchers → synthesiser flow | [`03-agentic-frameworks/01-langgraph`](leaves/03-agentic-frameworks/01-langgraph/index.md) | Same shape as the [`multi-agent-research-system`](https://github.com/your-handle/multi-agent-research-system/tree/main/) deep-dive |

---

## Healthcare / regulated documents — "Always require a human signoff"

> **Problem:** A clinical-summarisation agent must produce a draft but
> never publish without a clinician's review. The draft must include
> source page numbers for every claim. Latency budget: minutes, not
> seconds.

| Need | Leaf | What to change |
|---|---|---|
| Interrupt/resume across HTTP | [`04-human-in-the-loop/00-interrupt-and-resume`](leaves/04-human-in-the-loop/00-interrupt-and-resume/index.md) | The pattern survives a Kubernetes restart with the `PostgresSaver` checkpointer |
| Approval gate on publish | [`04-human-in-the-loop/01-approval-gates`](leaves/04-human-in-the-loop/01-approval-gates/index.md) | The clinician sees the draft + sources + a one-click approve/deny |
| Streaming UI with mid-run intervention | [`04-human-in-the-loop/04-streaming-with-intervention`](leaves/04-human-in-the-loop/04-streaming-with-intervention/index.md) | The clinician can edit the draft *while* the agent is still searching |
| Time-travel debugging | [`04-human-in-the-loop/03-time-travel-debug`](leaves/04-human-in-the-loop/03-time-travel-debug/index.md) | When a clinician disagrees, jump back to the retrieval step and re-run with a corrected query |
| Cite every claim | [`01-rag/11-long-context-rag`](leaves/01-rag/11-long-context-rag/index.md) | Contextual retrieval pattern; emits `[page 42]` style citations the UI renders inline |

---

## Multimodal — "PDF screenshots with tables + charts"

> **Problem:** Analysts paste in earnings PDFs and ask
> *"what did the CFO say about Q4 guidance?"* — the answer is in a
> table, not in the prose.

| Need | Leaf | What to change |
|---|---|---|
| Vision-model retrieval over page screenshots | [`01-rag/10-multimodal-rag`](leaves/01-rag/10-multimodal-rag/index.md) | The ColPali / Voyage Multimodal pattern handles tables-as-images without OCR pain |
| Late-interaction scoring | [`02-indexing/06-colbert-late-interaction`](leaves/02-indexing/06-colbert-late-interaction/index.md) | MaxSim's per-token scoring catches "CFO said X" where dense retrieval blurs it |

---

## Async / out-of-process HITL — "Approve from your Slack DM"

> **Problem:** Your agent runs a long-running job; the human reviewer
> doesn't have a browser open. They want to approve from Slack /
> email / a mobile push.

| Need | Leaf | What to change |
|---|---|---|
| Queue-based HITL (interrupt → durable queue → human responds asynchronously) | [`04-human-in-the-loop/05-async-hitl-via-queue`](leaves/04-human-in-the-loop/05-async-hitl-via-queue/index.md) | Replace the in-memory queue with SQS / Redis / Postgres advisory lock |
| State persists across the human-think delay | [`04-human-in-the-loop/02-edit-state`](leaves/04-human-in-the-loop/02-edit-state/index.md) | The reviewer can edit the draft via the Slack modal before approving |

---

## DevOps / runbook execution — "Don't drop the prod database"

> **Problem:** An ops agent runs runbooks. *Some* steps are
> read-only and can fire immediately; *some* steps (`DROP TABLE`,
> `kubectl delete ns`) require explicit human go-ahead.

| Need | Leaf | What to change |
|---|---|---|
| Per-tool approval policy | [`04-human-in-the-loop/01-approval-gates`](leaves/04-human-in-the-loop/01-approval-gates/index.md) | Decorate tools with `requires_approval=True`; read-only tools auto-approve |
| Edit a destructive command before it runs | [`04-human-in-the-loop/02-edit-state`](leaves/04-human-in-the-loop/02-edit-state/index.md) | Human can rewrite the SQL the agent proposed before approving |
| Audit log of every action | [`06-mcp/00-mcp-server-basics`](leaves/06-mcp/00-mcp-server-basics/index.md) | The MCP audit log doubles as the change-management record |

---

## How we measure all of the above

Every realistic use case above ultimately needs **the same five
guardrails** we built once:

1. **Faithfulness** — [`05-evals-and-observability/00-ragas-rag-eval`](leaves/05-evals-and-observability/00-ragas-rag-eval/index.md)
2. **Tool-call accuracy** — [`05-evals-and-observability/01-ragas-agent-eval`](leaves/05-evals-and-observability/01-ragas-agent-eval/index.md)
3. **Cost + latency** — [`05-evals-and-observability/06-cost-and-latency-bench`](leaves/05-evals-and-observability/06-cost-and-latency-bench/index.md)
4. **Regression gate in CI** — [`05-evals-and-observability/05-regression-suite`](leaves/05-evals-and-observability/05-regression-suite/index.md)
5. **Tracing** — [`05-evals-and-observability/02-langfuse-tracing`](leaves/05-evals-and-observability/02-langfuse-tracing/index.md)

The arXiv corpus is the dev environment for that whole machinery. Your
production corpus is a fork of `benchmarks/corpus/` + a fork of
`benchmarks/golden-qa/`; the rest of the hub doesn't care.
