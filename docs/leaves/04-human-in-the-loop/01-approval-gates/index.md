!!! info "`04-human-in-the-loop/01-approval-gates`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/your-handle/agentic-ai-engineering/tree/main/04-human-in-the-loop/01-approval-gates)

**Headline metrics:** _no headline metric_

# Approval gates — gate sensitive tool calls

**Problem:** Some tool calls have real-world consequences (sending an email, executing a SQL `DELETE`, transferring funds, publishing content). Letting the LLM decide unilaterally is unsafe; demanding manual approval for *every* tool call is unusable. You need a policy that interrupts only on the dangerous subset, with enough context for the reviewer to decide quickly.

**What you'll learn:**
- How to classify tool calls into `safe` / `requires_approval` / `forbidden`.
- The shape of an approval request: tool name, arguments, justification, blast radius.
- Why "approve once" vs "approve always" matter and how to encode them.
- A reusable approval-gate decorator that wraps any tool with a checkpointer interrupt.

**When to use it:** Any agent with destructive or visible side effects in production. Pairs naturally with audit logs.

**When NOT to use it:** Read-only or sandboxed tools, agents running entirely on the user's own machine where they already see every action.

## Run it

```powershell
uv run jupyter lab 04-human-in-the-loop/01-approval-gates/notebook.ipynb
uv run python 04-human-in-the-loop/01-approval-gates/eval.py
```

## Key results

The eval runs 3 demo questions × 2 reviewer policies (`approve_all`, `deny_all`)
to show the gate is symmetric. Tracked metrics: `approval_gate_fire_rate`,
`approval_policy_consistency`, `safe_tool_bypass_rate` (should be 1.0 — safe
tools must NOT trigger the gate), `avg_latency_ms`.

## References

- LangGraph: [Review tool calls before execution](https://langchain-ai.github.io/langgraph/how-tos/review-tool-calls/)
- Anthropic engineering blog: [Building effective agents — guardrails section](https://www.anthropic.com/research/building-effective-agents)
