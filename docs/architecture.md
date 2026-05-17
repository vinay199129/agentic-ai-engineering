# Architecture

System-level diagrams for the hub repo. Each leaf has its own focused
diagram in its README — these are the cross-cutting views.

## The leaf shape — every folder ships the same four artefacts

```mermaid
flowchart LR
    R[README.md] --> NB[notebook.ipynb]
    NB --> E[eval.py]
    E --> S[eval-snapshot.json]
    S -.committed.-> CI[.github/workflows/regression]
    CI -.fails PR if >5% drop.-> R
```

## Layered dependency graph between phases

```mermaid
flowchart TD
    F[Phase 0<br/>Scaffolding]
    F1[Phase 1<br/>Foundations + naive RAG]
    F2[Phase 2<br/>Advanced RAG x12]
    F3[Phase 3<br/>Indexing internals]
    F4[Phase 4<br/>Evals + observability]
    F5[Phase 5<br/>Agentic frameworks tour]
    F6[Phase 6<br/>HITL]
    F7[Phase 7<br/>MCP]
    F8[Phase 8<br/>Deployment]
    F --> F1 --> F2
    F --> F3
    F1 --> F4
    F4 -.regression suite gates.-> F2 & F3 & F5
    F1 --> F5 --> F6
    F5 --> F7
    F6 --> F8
    F7 --> F8
```

## Runtime architecture of the deployment stack

The five Phase 8 leaves compose into a working dev environment:

```mermaid
flowchart LR
    subgraph Browser
        UI[Next.js chat<br/>leaf 04 — edge runtime]
    end
    subgraph FastAPI[Python services]
        API[FastAPI agent<br/>leaf 00]
        ST[Streamlit demo<br/>leaf 01]
    end
    subgraph Stateful[Stateful infra — leaf 02 docker compose]
        PG[(Postgres + pgvector)]
        RD[(Redis)]
        LF[Langfuse]
    end
    HF[HF Space<br/>leaf 03]

    UI -- SSE proxy --> API
    UI -- POST resume --> API
    ST -- in-process --> API
    API -- vectors + checkpoints --> PG
    API -- cache + pub/sub --> RD
    API -- spans --> LF
    LF --> PG
    HF -. auto-publishes .- ST
```

## The shared LLM shim — why CI never needs API keys

```mermaid
sequenceDiagram
    participant Notebook
    participant shim as shared/llm.py
    participant cache as .llm-cache/
    participant live as LiteLLM provider

    Notebook->>shim: complete(prompt, model)
    alt LLM_CACHE_ONLY=1 (CI)
        shim->>cache: hash(prompt, model)
        cache-->>shim: cached response
        shim-->>Notebook: response
    else live mode
        shim->>live: API call
        live-->>shim: response
        shim->>cache: store(hash, response)
        shim-->>Notebook: response
    end
```

## HITL interrupt-and-resume — the pattern that survives HTTP

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Next.js
    participant API as FastAPI
    participant G as hitl.Graph
    participant CP as Checkpointer

    U->>UI: ask
    UI->>API: GET /agent/stream (SSE)
    API->>G: run(state)
    G->>CP: put(step n)
    G->>API: yield node_complete
    API->>UI: SSE frame
    G->>API: yield interrupt
    API->>UI: SSE frame
    UI->>U: show approve/deny
    U->>UI: approve
    UI->>API: POST /agent/resume
    API->>G: resume(Command)
    G->>CP: put(step n+2)
    G->>API: final state
    API->>UI: complete frame
```

## MCP — three primitives that map cleanly to LangChain abstractions

```mermaid
flowchart LR
    subgraph Server[MCP Server]
        T[Tools<br/>callable]
        Rs[Resources<br/>URI addressable]
        P[Prompts<br/>parameterised templates]
    end
    subgraph Client[MCP Client]
        I[initialize]
        TL[tools/list + tools/call]
        RL[resources/list + resources/read]
        PL[prompts/list + prompts/get]
    end
    I --> Server
    T --- TL
    Rs --- RL
    P --- PL
```
