# IVF-PQ — Inverted File Index + Product Quantization

**Problem:** HNSW gives you sub-ms search but stores every vector in RAM. At 100M docs × 1536 dims × 4 bytes that's 600 GB. IVF-PQ flips the tradeoff: partition the space (IVF) so you only scan a fraction of it, then compress each vector to ~32 bytes (PQ) so the whole index fits in tens of GB.

**What you'll learn:**
- **IVF** — k-means partition + `nprobe` cell visits. The recall/latency knob lives in `nprobe`.
- **PQ** — split each vector into `M` sub-spaces, quantize each to `k*` centroids, store an `M`-byte code per vector. Memory savings often 16–32×.
- **ADC (Asymmetric Distance Computation)** — at query time, precompute one distance table per sub-space; lookup beats decode.
- The IVF-PQ recall/memory tradeoff on the canonical Q&A — small here, but the pattern generalises.

**When to use it:** Billion-scale corpora; RAM-constrained deployments; offline/batch retrieval where 1–5% recall loss is acceptable. This is FAISS's default for big indexes.

**When NOT to use it:** Small corpora (< 1M) — Flat or HNSW are simpler and lossless-enough. Strict-recall use cases (legal discovery, biomedical safety) where missing 2% of relevant docs is unacceptable.

## Run it

```powershell
uv sync --group indexing
uv run jupyter lab 02-indexing/02-ivf-pq-quantization/notebook.ipynb
uv run python 02-indexing/02-ivf-pq-quantization/eval.py
```

No LLM calls.

## Key results

See [`eval-snapshot.json`](./eval-snapshot.json) for: per-`nprobe` IVF recall, PQ approximation recall, and the memory ratio (original float32 vs PQ codes). At `nprobe=nlist` IVF degenerates to Flat (sanity check).

## References

- Jégou, Douze & Schmid, [Product Quantization for Nearest Neighbor Search](https://hal.inria.fr/inria-00514462v2/document)
- Babenko & Lempitsky, [The Inverted Multi-Index](https://cmp.felk.cvut.cz/~toliageo/p/babenko-inverted-multi-index.pdf)
- [FAISS IVFPQ tutorial](https://github.com/facebookresearch/faiss/wiki/Lower-memory-footprint)
