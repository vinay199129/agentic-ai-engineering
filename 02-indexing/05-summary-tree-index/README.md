# Summary-tree index — hierarchical retrieval

**Problem:** A flat vector index retrieves *chunks*; you ask it "what's in the corpus?" and it has nothing to say. A summary-tree index goes one level up — it summarises each document, clusters those summaries into topic groups, and summarises each group. Queries route first at cluster level (cheap, global) and drill into leaves only when needed.

**What you'll learn:**
- Three-level tree: leaf summaries → cluster summaries → cluster routing.
- The retrieval pattern: dense-route at cluster level, then dense-retrieve inside the chosen cluster.
- How this compares to flat dense retrieval on a small corpus (often the tree loses on tiny corpora and wins as the corpus grows).
- The intuition behind LlamaIndex's `SummaryIndex` / `tree_summarize` response mode.

**When to use it:** Large corpora where pre-summarised cluster context helps the LLM orient itself, hierarchical content (e.g., book → chapter → section), and "global" questions about *what's in the corpus*.

**When NOT to use it:** Small corpora — building the tree costs more than it saves. Workloads dominated by exact-keyword recall (use BM25 / hybrid).

## Run it

```powershell
uv sync --group indexing
uv run jupyter lab 02-indexing/05-summary-tree-index/notebook.ipynb
uv run python 02-indexing/05-summary-tree-index/eval.py
```

The notebook uses cached LLM responses (`LLM_CACHE_ONLY=1`) by default. The eval reuses cached leaf summaries and is fully deterministic.

## Key results

See [`eval-snapshot.json`](./eval-snapshot.json) for tree vs flat `recall@3` plus the cluster shape (how many docs per cluster).

## References

- [LlamaIndex `SummaryIndex`](https://docs.llamaindex.ai/en/stable/module_guides/indexing/index_guide/#summary-index)
- Liu et al., [LangChain RAG: hierarchical summarization](https://blog.langchain.dev/long-context-retrieval/)
- Anthropic, [Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval) (orthogonal — leaf-level context vs. tree-level routing)
