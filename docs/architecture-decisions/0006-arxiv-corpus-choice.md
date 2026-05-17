# 0006 — arXiv `cs.CL` as the canonical demo corpus

- **Status:** accepted
- **Date:** 2025-12-06
- **Context:** Every leaf in the hub needs the same underlying
  document set for snapshots to be comparable. We need a corpus that
  is **freely redistributable**, **factually rich** (good for RAG
  faithfulness checks), **non-trivial** (entities, relationships,
  jargon — good for GraphRAG), and **legible to a technical
  audience** (a recruiter or engineer can sanity-check answers).
- **Decision:** Use a curated slice of **arXiv `cs.CL` abstracts +
  full-text PDFs** from 2023–2025 as the canonical corpus. The
  download script lives in `benchmarks/corpus/`; the corpus itself
  is git-ignored. Golden Q&A lives in `benchmarks/golden-qa/`.
- **Consequences:**
  - **Good** — Public, citeable, free of licensing landmines. Rich
    entity layer (papers, authors, methods, datasets) — exactly the
    profile GraphRAG was built for. Audience already knows roughly
    what to expect, which makes wrong answers easy to spot.
  - **Good** — The cs.CL slice is small enough (~500 papers in our
    cut) that index builds finish in minutes, but rich enough that
    snapshots are non-trivial. Re-running the full eval matrix on a
    laptop is feasible.
  - **Bad** — The corpus is in-distribution for nearly every modern
    LLM. RAG faithfulness numbers may look slightly better than they
    would on private data. We flag this prominently in the relevant
    leaves' READMEs.
  - **Bad** — Not representative of enterprise document chaos
    (tables, forms, layouts). For those concerns the hub points
    readers to the production-rag-pipeline deep-dive repo, which
    uses a messier corpus.
- **Alternatives considered:**
  - **HotpotQA / MS MARCO** — Great benchmarks; built for QA, not
    for the indexing / agentic patterns we want to showcase.
  - **Private synthetic corpus** — Maximally honest about LLM blind
    spots; minimum legibility. Rejected for a portfolio context.
  - **Wikipedia subset** — Too in-distribution; too well-trodden.
