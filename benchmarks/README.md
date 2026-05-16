# benchmarks/

Shared eval datasets and leaderboards consumed across topic folders. **Data files are git-ignored**; only download scripts and curated metadata are committed.

## Layout *(populated in Phase 1)*

```
benchmarks/
├── corpus/
│   ├── download.py          # fetches arxiv-cs.CL ~500 papers, last 2 years
│   └── metadata.jsonl       # title, abstract, arxiv id, year — committed
├── golden-qa/
│   └── v1.jsonl             # ~50 hand-curated Q&A pairs — committed
└── synthetic-qa/
    └── v1.jsonl             # RAGAS-generated, ~250 pairs — committed (small)
```

## Canonical corpus

**arxiv-cs.CL** — Computation and Language papers, last 2 years, ~500 documents. Chosen because:

- Domain is impressive for AI roles
- Freely downloadable, manageable size
- Realistic chunking challenges (figures, equations, references)
- Used across all RAG and indexing leaves so results are comparable
