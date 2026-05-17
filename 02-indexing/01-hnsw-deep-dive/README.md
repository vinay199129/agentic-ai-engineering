# HNSW from scratch — Hierarchical Navigable Small World graphs

**Problem:** Brute-force cosine over 100M vectors takes seconds — far too slow for interactive search. HNSW is the algorithm every production vector DB (pgvector, Qdrant, Weaviate, Milvus, Pinecone, FAISS-HNSW) uses to drive that latency to sub-millisecond at ≈95% recall.

**What you'll learn:**
- The two ideas that make HNSW work: a randomized layered graph + greedy descent from a sparse top layer down to a dense bottom layer.
- `M`, `ef_construction`, `ef_search` — what each does and how they trade recall for latency/memory.
- A pure-numpy implementation of insert + search that follows Malkov & Yashunin (2016) Algorithm 1.
- A `matplotlib` plot of the layered graph so the algorithm stops being a black box.

**When to use it:** Anywhere you need approximate-nearest-neighbour search with high recall, low latency, and the ability to insert nodes online. This is the default index for any production vector DB.

**When NOT to use it:** When you need exact answers (use Flat), when RAM is too tight for the in-memory graph (use IVF-PQ; see `../02-ivf-pq-quantization/`), or when the workload is dominated by lexical match (use BM25).

## Run it

```powershell
uv sync --group indexing
uv run jupyter lab 02-indexing/01-hnsw-deep-dive/notebook.ipynb
uv run python 02-indexing/01-hnsw-deep-dive/eval.py
```

No LLM calls. The notebook also writes `hnsw_layers.png` so you can eyeball the layered graph.

## Key results

See [`eval-snapshot.json`](./eval-snapshot.json) for the `ef_search` sweep: recall vs flat ground truth at `ef ∈ {1, 2, 4, 8, 16}`. With `M=4` on 10 vectors, `ef=8` already reaches 1.0; on a real 1M-vector corpus the gap between `ef=16` and `ef=200` becomes the recall/latency dial you actually tune.

## References

- Malkov & Yashunin, [Efficient and robust ANN search using Hierarchical Navigable Small World graphs](https://arxiv.org/abs/1603.09320)
- [Faiss HNSW notes](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes#hnsw)
- [Qdrant HNSW tuning guide](https://qdrant.tech/articles/hnsw-tuning/)
