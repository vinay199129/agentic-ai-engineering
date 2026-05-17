# 07 — Deployment patterns

Ship-ready patterns for serving agents and RAG systems. One TypeScript sub-project for stack breadth.

## Planned leaves

| Leaf | Topic | Status |
|---|---|---|
| `00-fastapi-streaming-agent/` | SSE endpoint + interrupt-and-resume HITL wiring | ✅ |
| `01-streamlit-demo-template/` | Reusable shell with pluggable `solve_fn` | ✅ |
| `02-docker-compose-stack/` | API + Postgres+pgvector + Langfuse + Redis | ✅ |
| `03-hf-spaces-deploy/` | Streamlit Space + CI workflow that auto-republishes | ✅ |
| `04-ts-vercel-ai-sdk-chat/` | Next.js (App Router, edge runtime) proxying SSE from the FastAPI backend | ✅ |

## How the leaves compose

```
┌────────────────────┐    SSE      ┌──────────────────────────┐
│  04 — Next.js UI   │ ──────────▶ │  00 — FastAPI agent      │
│  (edge proxy)      │ ◀─POST───── │  (interrupt + resume)    │
└────────────────────┘             └──────────────┬───────────┘
                                                  │
       ┌─────────────────────┬───────────────────┴────────────┐
       ▼                     ▼                                ▼
┌─────────────┐      ┌───────────────┐                ┌──────────────┐
│ Postgres    │      │ Redis cache   │                │ Langfuse     │
│ + pgvector  │      │ + pub/sub     │                │ (tracing)    │
└─────────────┘      └───────────────┘                └──────────────┘
                  02 — Docker Compose stack
```

The Streamlit template (01) and HF Spaces deploy (03) share a public demo
target so a recruiter can click straight from the hub README to a live
agent.
