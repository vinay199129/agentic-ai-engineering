!!! info "`02-indexing/07-incremental-indexing`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/vinay199129/agentic-ai-engineering/tree/main/02-indexing/07-incremental-indexing)

**Headline metrics:** _no headline metric_

# Incremental indexing — adds, deletes, tombstones, re-embeds

**Problem:** Real corpora aren't built once and frozen. Documents get added, deleted, edited; embeddings get re-computed when the model changes. A production index has to handle all of that without a full rebuild — and you need to know what each mutation does to recall.

**What you'll learn:**
- The five operations every production vector index supports: `add`, `delete`, `update`, `rebuild`, `re-embed`.
- **Tombstoning** — the lazy-delete strategy used by FAISS/HNSW (marker bit + filter at query time).
- The cost of *not* re-embedding: when you switch embedding models, a partially re-embedded index has a recall cliff.
- Why "delta indexing" (small new HNSW shard merged at query time) is the default for stream-ingested corpora.

**When to use this knowledge:** Any time you're picking a vector DB for a workload with > 1% daily churn. Compare each DB's claimed support for online insert, delete, and re-embed.

**When NOT to fuss with this:** Read-only corpora (most demo apps, RAG over a static doc set). For those, rebuild is fine.

## Run it

```powershell
uv sync --group indexing
uv run jupyter lab 02-indexing/07-incremental-indexing/notebook.ipynb
uv run python 02-indexing/07-incremental-indexing/eval.py
```

No LLM calls.

## Key results

See [`eval-snapshot.json`](https://github.com/vinay199129/agentic-ai-engineering/blob/main/02-indexing/07-incremental-indexing/./eval-snapshot.json) for: baseline recall, recall after deletes-with-tombstones, recall after adding new docs, and the recall cliff when half the index is re-embedded with a new model (seed change) — i.e., the mixed-embedder failure mode.

## References

- [FAISS — IndexIDMap & removeIds](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes#indexidmap)
- [Qdrant — payload-aware deletes](https://qdrant.tech/documentation/concepts/points/#delete-points)
- [Milvus — incremental indexing](https://milvus.io/blog/2022-09-26-how-milvus-supports-incremental-indexing.md)
- Pinecone, [Hot/cold tiers and re-embedding](https://www.pinecone.io/learn/series/faiss-vs-pinecone/)
