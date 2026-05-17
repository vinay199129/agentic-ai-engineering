!!! info "`01-rag/10-multimodal-rag`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/vinay199129/agentic-ai-engineering/tree/main/01-rag/10-multimodal-rag)

**Headline metrics:** _no headline metric_

# Multimodal RAG — joint text + figure retrieval

**Problem:** Papers, decks, PDFs, and product pages have figures. A text-only retriever throws them away. The user's question ("show me the bar chart of expert utilization") then has no signal to match on.

**What you'll learn:**
- Generate one synthetic matplotlib figure per abstract (deterministic, reproducible from a fixed seed).
- Embed each figure with a hash-based stand-in that has the same interface as CLIP/SigLIP (`np.ndarray` of shape `(dims,)`, L2-normalized).
- Build a **joint embedding** by averaging text + image vectors — works because both are normalized.
- Side-by-side retrieval: text-only vs joint. Joint acts as a tie-breaker on ambiguous text queries.

This leaf is intentionally offline-deterministic — no API key, no network. Swap `img_embed` for `clip-vit-base-patch32` to make it real.

**When to use it:** Any corpus where figures carry information the captions don't (charts, diagrams, screenshots, slide decks).

**When NOT to use it:** Pure text corpora. Or when you have OCR / VLM captions covering the same signal.

## Run it

```powershell
uv sync --group rag
uv run jupyter lab 01-rag/10-multimodal-rag/notebook.ipynb
uv run python 01-rag/10-multimodal-rag/eval.py
```

Figures are written to `01-rag/10-multimodal-rag/figures/` (regenerated on every run; not committed).

## Key results

See [`eval-snapshot.json`](https://github.com/vinay199129/agentic-ai-engineering/blob/main/01-rag/10-multimodal-rag/./eval-snapshot.json) for per-modality recall@k on the answerable Q&A.

## References

- Radford et al., [Learning Transferable Visual Models From Natural Language Supervision (CLIP)](https://arxiv.org/abs/2103.00020)
- [SigLIP](https://huggingface.co/docs/transformers/en/model_doc/siglip)
- [Anthropic Vision in Claude](https://docs.anthropic.com/en/docs/build-with-claude/vision)
