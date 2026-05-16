# 04 — Human-in-the-loop

Production-grade HITL patterns. Primarily LangGraph (`interrupt()` + checkpointer), with one CrewAI example for breadth.

## Planned leaves

| Leaf | Pattern | Status |
|---|---|---|
| `00-interrupt-and-resume/` | LangGraph `interrupt()` + resume with `Command` | ⏳ Phase 6 |
| `01-approval-gates/` | Tool-call approval before execution | ⏳ Phase 6 |
| `02-edit-state/` | Inspect & modify graph state mid-run | ⏳ Phase 6 |
| `03-time-travel-debug/` | Checkpoint rewind / fork | ⏳ Phase 6 |
| `04-streaming-with-intervention/` | Pause stream → user input → resume | ⏳ Phase 6 |
| `05-async-hitl-via-queue/` | Long-running agent + email/Slack approval webhook | ⏳ Phase 6 |
