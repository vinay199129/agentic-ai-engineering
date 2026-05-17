# Framework comparison — same task, 7 implementations

**Problem:** Picking an agent framework is a high-switching-cost decision. The honest comparison is "implement the same task in each and read the diffs", which is exactly what this folder is for. This leaf aggregates the snapshots from the six framework leaves (plus the from-scratch ReAct baseline) into one side-by-side view.

**What you'll learn:**
- A **feature matrix** across the seven: typed I/O, graph state, conditional edges, streaming, checkpointer, code-action, handoffs.
- An opinionated commentary on **when to pick which** based on task shape (single-tool / multi-step pipeline / branchy / multi-agent debate / code reasoning).
- A leaderboard auto-built from the sibling `eval-snapshot.json` files — every snapshot's `averages` block is the same shape, so the table is honest.

**When to use it:** Once you've read at least three of the framework leaves. This is the synthesis; the leaves are the data.

**When NOT to use it:** As your *first* exposure to agent frameworks — read `00-react-from-scratch/` first, then one of the typed frameworks (`02-pydantic-ai/`), then come back here.

## Run it

```powershell
uv run python 03-agentic-frameworks/07-framework-comparison/eval.py
```

Produces `eval-snapshot.json` + `leaderboard.md`.

## Key results

See [`leaderboard.md`](./leaderboard.md) for the per-framework table and [`eval-snapshot.json`](./eval-snapshot.json) for the structured form.

## References

- See each sibling leaf for its individual framework's References section.
