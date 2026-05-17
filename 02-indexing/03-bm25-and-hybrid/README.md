# BM25 internals and hybrid retrieval — deep dive

**Problem:** `01-rag/03-hybrid-search/` *uses* hybrid retrieval. This leaf opens up *why* it works — the BM25 saturation curve, the IDF and length normalisation knobs, and how RRF compares to a weighted-α fusion you'd tune yourself.

**What you'll learn:**
- The BM25 formula in code, with `k1` (TF saturation) and `b` (length norm) wired in so you can flip them.
- TF-IDF as the degenerate case `k1 → ∞, b → 0`, and why it usually loses.
- **Reciprocal Rank Fusion** as the parameter-free hybrid combiner: `score(d) = Σ 1 / (k + rank_i(d))`.
- **Weighted linear fusion** `α · dense + (1 − α) · bm25` with an α sweep so the tradeoff is visible.
- When BM25 helps (entity / acronym queries) and when it hurts (paraphrase-only corpora).

**When to use it:** Re-read this leaf any time you need to justify a retriever choice or tune `k1`, `b`, `alpha`, or `k_rrf` on a new corpus.

**When NOT to use it:** As a production retriever — for that, use `01-rag/03-hybrid-search/`. This leaf is the explanation, not the deployment.

## Run it

```powershell
uv sync --group indexing
uv run jupyter lab 02-indexing/03-bm25-and-hybrid/notebook.ipynb
uv run python 02-indexing/03-bm25-and-hybrid/eval.py
```

No LLM calls. The notebook writes `fusion_sweep.png` for the α sweep.

## Key results

See [`eval-snapshot.json`](./eval-snapshot.json) for `recall@{1,3,5}` across BM25 / TF-IDF / dense / RRF / best-α weighted fusion, plus the `α*` that maximises recall@3 on the golden Q&A.

## References

- Robertson & Zaragoza, [The Probabilistic Relevance Framework: BM25 and Beyond](https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf)
- Cormack et al., [Reciprocal Rank Fusion outperforms Condorcet and individual rank learning methods](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
- [Elastic explanation of BM25](https://www.elastic.co/blog/practical-bm25-part-2-the-bm25-algorithm-and-its-variables)
