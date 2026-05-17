# RAGAS-style RAG eval — faithfulness, context precision, context recall, answer relevancy

**Problem:** A RAG pipeline can fail in five distinct ways — wrong context retrieved, right context but missed, fabrications not in the context, off-topic answers, refusal-when-it-shouldn't. A single metric like recall@k catches one of them. RAGAS bundles the four LLM-graded metrics that catch the rest.

**What you'll learn:**
- **Context Precision** — of the chunks retrieved, how many are actually relevant?
- **Context Recall** — of the relevant chunks in the corpus, how many did we retrieve?
- **Faithfulness** — every claim in the answer is supported by the retrieved context (anti-hallucination).
- **Answer Relevancy** — does the answer actually address the question?
- Each metric implemented from scratch on top of `shared.llm.complete()` so the eval is cache-friendly and the prompts are visible (no library black box).

**When to use it:** Before *every* production change to retrieval, prompting, or model. The four metrics map to four very different failure modes — track all four, not just one.

**When NOT to use it:** When you have ground-truth answers and can use direct exact-match / BLEU / ROUGE / EM-F1 metrics — those are cheaper and judge-free. RAGAS metrics earn their cost on open-ended generation.

## Run it

```powershell
uv sync --group evals
uv run jupyter lab 05-evals-and-observability/00-ragas-rag-eval/notebook.ipynb
uv run python 05-evals-and-observability/00-ragas-rag-eval/eval.py
```

The notebook + eval call the four metrics via `shared.llm.complete()`. With `LLM_CACHE_ONLY=1` (the CI default) judge calls replay from `.llm-cache/`; if a key is missing the metric falls back to a deterministic heuristic so the snapshot is always produced.

## Key results

See [`eval-snapshot.json`](./eval-snapshot.json) for: per-metric average across the answerable golden Q&A subset (q01–q26), plus a per-question breakdown for a 5-question demo set.

## References

- ES et al., [RAGAS: Automated Evaluation of Retrieval Augmented Generation](https://arxiv.org/abs/2309.15217)
- [RAGAS docs — Faithfulness / Context Precision / Recall](https://docs.ragas.io/en/stable/concepts/metrics/index.html)
- TruLens / DeepEval — alternative LLM-judge stacks worth comparing
