# Architecture Decision Records (ADRs)

Lightweight ADRs for non-obvious choices in this repo. Each decision lives in its own file: `NNNN-short-title.md`.

## Format

```markdown
# NNNN — Short title

- **Status:** proposed | accepted | superseded by NNNN
- **Date:** YYYY-MM-DD
- **Context:** why is this decision needed?
- **Decision:** what we chose.
- **Consequences:** good and bad.
- **Alternatives considered:** what we rejected and why.
```

## Planned ADRs *(written as phases ship)*

- `0001-uv-over-poetry.md` — package manager choice
- `0002-pgvector-over-dedicated-vector-db.md` — single-store decision (for `production-rag-pipeline`)
- `0003-langgraph-over-crewai-for-deep-dive-2.md` — framework choice for the multi-agent system
- `0004-self-hosted-langfuse.md` — observability stack
- `0005-mcp-only-tools-in-deep-dive-2.md` — proving MCP fluency vs. native tools
- `0006-arxiv-corpus-choice.md` — canonical demo corpus
