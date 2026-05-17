!!! info "`07-deployment-patterns/04-ts-vercel-ai-sdk-chat`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/vinay199129/agentic-ai-engineering/tree/main/07-deployment-patterns/04-ts-vercel-ai-sdk-chat)

**Headline metrics:** _no headline metric_

# TypeScript chat UI — Next.js + Vercel AI SDK streaming from the FastAPI backend

**Problem:** Streamlit is great for internal demos but is the wrong tool for a polished public UI: it rebuilds on every interaction, doesn't share state nicely between users, and the design language is fixed. **Next.js on Vercel** + the **Vercel AI SDK** is the production answer — same-origin SSE proxying, edge runtime, and React you can theme.

**What you'll learn:**
- The two-tier deploy pattern: **stateful agent** (FastAPI on a real server) + **stateless edge UI** (Next.js on Vercel). The UI proxies SSE through `/api/chat` so the browser sees a same-origin stream — no CORS, no cookie weirdness.
- How to consume *structured graph events* (`node_complete`, `interrupt`, …) — `useChat` from `ai/react` only knows OpenAI completion frames, so we hand-roll a tiny SSE reader.
- The interrupt-and-resume UX: when the backend emits `interrupt`, the UI shows an approve/deny panel and POSTs the decision to `/agent/resume`.
- Vercel-friendly environment plumbing: `AGENT_BACKEND_URL` (server-side) and `NEXT_PUBLIC_AGENT_BACKEND_URL` (browser).

**When to use it:** Public-facing chat surfaces, anything you'd put in front of >50 users.

**When NOT to use it:** Quick internal demos — use Streamlit (leaf 01) and skip the JS toolchain.

## Layout

```
04-ts-vercel-ai-sdk-chat/
├── package.json
├── tsconfig.json
├── src/app/
│   ├── layout.tsx
│   ├── page.tsx                # client component: streams from /api/chat
│   └── api/chat/route.ts       # edge route: proxies SSE from backend
└── eval.py                     # config-shape validation (Python so CI is uniform)
```

## Run it

```powershell
# Terminal 1 — Python agent backend (leaf 00):
uv run uvicorn 07-deployment-patterns.00-fastapi-streaming-agent.app:app --reload

# Terminal 2 — Next.js UI:
cd 07-deployment-patterns/04-ts-vercel-ai-sdk-chat
npm install
$Env:AGENT_BACKEND_URL = "http://localhost:8000"
$Env:NEXT_PUBLIC_AGENT_BACKEND_URL = "http://localhost:8000"
npm run dev          # → http://localhost:3001
```

CI/offline structural check:

```powershell
uv run python 07-deployment-patterns/04-ts-vercel-ai-sdk-chat/eval.py
```

## Key results

The eval parses `package.json`, verifies the dependency set (`ai`, `next`,
`react`), the required scripts (`dev`, `build`, `lint`, `typecheck`), and
checks the App Router files exist with the expected exports/runtime.
Tracked metrics: `package_json_parses`, `required_deps_present`,
`required_scripts_present`, `app_router_files_present`,
`edge_runtime_declared`.

## References

- [Vercel AI SDK](https://sdk.vercel.ai/docs)
- [Next.js App Router — streaming](https://nextjs.org/docs/app/building-your-application/routing/loading-ui-and-streaming)
