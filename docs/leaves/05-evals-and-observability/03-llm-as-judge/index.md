!!! info "`05-evals-and-observability/03-llm-as-judge`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/vinay199129/agentic-ai-engineering/tree/main/05-evals-and-observability/03-llm-as-judge)

**Headline metrics:** _no headline metric_

# LLM-as-judge — rubric, pairwise, position-swap bias mitigation

**Problem:** Once you're evaluating open-ended generation, ground truth doesn't exist — you have to ask a stronger model to grade. But naive LLM-judge has well-documented biases: position bias (prefers the first answer), verbosity bias (prefers longer answers), self-preference, and miscalibration.

**What you'll learn:**
- **Rubric judging** — score against a fixed numeric/categorical rubric. Cheapest. Use for absolute scores.
- **Pairwise judging** — pick the better of two answers. More reliable than absolute scoring.
- **Position-swap mitigation** — call the pairwise judge *twice* with answers swapped; only count a win if it survives the swap.
- The three failure modes that LLM judges should be screened for: agreement-with-human, position-bias delta, verbosity-bias delta.

**When to use it:** Any time you need to compare two RAG pipelines / two prompts / two models on open-ended output. Pair this with the four-metric RAGAS suite (see `../00-ragas-rag-eval/`) — different layers of signal.

**When NOT to use it:** When you have a deterministic verifier (regex, SQL, unit test, exact-match). Always prefer code over LLMs when the answer space allows it.

## Run it

```powershell
uv sync --group evals
uv run jupyter lab 05-evals-and-observability/03-llm-as-judge/notebook.ipynb
uv run python 05-evals-and-observability/03-llm-as-judge/eval.py
```

Cached LLM judges + deterministic fallbacks; runs offline.

## Key results

See [`eval-snapshot.json`](https://github.com/vinay199129/agentic-ai-engineering/blob/main/05-evals-and-observability/03-llm-as-judge/./eval-snapshot.json) for: rubric-score histogram on a 5-pair fixture, pairwise win rate (raw vs position-swap-adjusted), and the **position-bias delta** that quantifies the cost of NOT swapping.

## References

- Zheng et al., [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena](https://arxiv.org/abs/2306.05685)
- Wang et al., [Large Language Models are not Fair Evaluators](https://arxiv.org/abs/2305.17926) — coins "position bias"
- Anthropic, [Building reliable evals](https://www.anthropic.com/news/evaluating-ai-systems)
