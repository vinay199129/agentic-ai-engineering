!!! info "`04-human-in-the-loop/02-edit-state`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/your-handle/agentic-ai-engineering/tree/main/04-human-in-the-loop/02-edit-state)

**Headline metrics:** _no headline metric_

# Edit state — fix the agent's draft instead of approving/denying

**Problem:** Sometimes the agent's tool call is right in *spirit* but wrong in *detail* — wrong arxiv id, sloppy citation, missing field. Forcing a binary approve/deny round-trips through the LLM and wastes budget. Letting the reviewer **edit** the state in place gets the right answer in one human action.

**What you'll learn:**
- The state-edit pattern: `Command(update={'draft': new_draft, 'approved': True})`.
- Why merging deltas (instead of replacing whole state) keeps non-edited keys safe.
- How to record the edit in the trace so audits can see human-vs-LLM contributions.
- Conflict shape: human edits an obsolete field — what does the next node observe?

**When to use it:** Whenever the reviewer is a domain expert and `re-run with feedback` would be more expensive than `apply patch and continue`.

**When NOT to use it:** Untrusted reviewers (they shouldn't get raw state write access; gate behind a schema-validating proxy).

## Run it

```powershell
uv run jupyter lab 04-human-in-the-loop/02-edit-state/notebook.ipynb
uv run python 04-human-in-the-loop/02-edit-state/eval.py
```

## Key results

For each demo question the eval injects a `Command(update=...)` that rewrites
the draft to a known-correct citation, then resumes. Tracked metrics:
`edit_applied_rate` (every interrupt should accept the edit),
`edit_propagation_accuracy` (downstream `publish` node must see the edited
value), `human_decision_accuracy`, `avg_latency_ms`.

## References

- LangGraph: [Edit graph state](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/#edit-graph-state)
- LangGraph reference: [`Command(update=...)`](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.Command)
