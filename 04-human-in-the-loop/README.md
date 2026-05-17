# 04 — Human-in-the-loop

Production-grade HITL patterns. Primarily LangGraph (`interrupt()` + checkpointer), with one CrewAI example for breadth.

## Planned leaves

| Leaf | Pattern | Status |
|---|---|---|
| `00-interrupt-and-resume/` | LangGraph `interrupt()` + resume with `Command` | ✅ |
| `01-approval-gates/` | Tool-call approval before execution | ✅ |
| `02-edit-state/` | Inspect & modify graph state mid-run | ✅ |
| `03-time-travel-debug/` | Checkpoint rewind / fork | ✅ |
| `04-streaming-with-intervention/` | Pause stream → user input → resume | ✅ |
| `05-async-hitl-via-queue/` | Long-running agent + email/Slack approval webhook | ✅ |

All leaves share `04-human-in-the-loop/hitl.py` — a tiny pure-Python runner
that mirrors LangGraph's `interrupt()` / `Command` / `Checkpointer` API so the
notebooks reproduce in CI without the framework.
