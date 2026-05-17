# Vector-DB comparison — Flat · HNSW · IVF · BM25

**Problem:** "Which index should I use?" has no single answer — it depends on corpus size, query mix, update frequency, and how much recall loss you can tolerate. This leaf benchmarks four canonical structures side-by-side so the tradeoffs aren't abstract.

**What you'll learn:**
- The four index families that every production vector DB ships under the hood: brute-force flat, HNSW graph, IVF (k-means partition), BM25 (lexical).
- Scratch implementations in numpy/sklearn — small enough to read in one sitting, big enough to show the recall/latency tradeoff.
- A shared `recall@{1,3,5}` bench across all four on the same Q&A so the comparison is apples-to-apples.

**When to use it:** Pick a leaf based on your scale and constraints — `< 10k` docs → Flat; large + RAM-bound → IVF/PQ (see `../02-ivf-pq-quantization/`); large + latency-bound → HNSW (see `../01-hnsw-deep-dive/`); entity-heavy queries → BM25 (see `../03-bm25-and-hybrid/`).

**When NOT to use this leaf's code in production:** the scratch HNSW/IVF are pedagogical. Use `hnswlib`, FAISS, pgvector, Qdrant, etc. for real workloads.

## Run it

```powershell
uv sync --group indexing
uv run jupyter lab 02-indexing/00-vector-db-comparison/notebook.ipynb
uv run python 02-indexing/00-vector-db-comparison/eval.py
```

No LLM calls; runs anywhere.

## Key results

See [`eval-snapshot.json`](./eval-snapshot.json) for per-index `recall@{1,3,5}` and build-time-ms on the canonical 10-doc corpus. On a corpus this small the recall differences are mostly noise — the real point is that the framework supports plugging in a 500-doc or 50M-doc corpus and reading the same metrics back.

## References

- Malkov & Yashunin, [HNSW: efficient and robust ANN search](https://arxiv.org/abs/1603.09320)
- Jegou et al., [Product Quantization for nearest neighbour search](https://hal.inria.fr/inria-00514462v2/document)
- [FAISS index taxonomy](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes)
- [pgvector index types](https://github.com/pgvector/pgvector#indexing)
