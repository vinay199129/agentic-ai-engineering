# benchmarks/corpus/

Canonical hub corpus.

## What ships in git

* `download.py` — fetches arxiv-cs.CL papers (last 2 years, ~500 by default).
* `metadata.jsonl` — **a 10-document synthetic seed corpus** so notebooks, tests, and CI run offline. Each `arxiv_id` is prefixed `synth-` to make its synthetic nature obvious.

## Real corpus locally

```bash
uv sync --group corpus
uv run python benchmarks/corpus/download.py --max 500
```

That overwrites `metadata.jsonl` with real arxiv data. The `golden-qa/v1.jsonl` set is grounded in the **synthetic** seed corpus on purpose so eval snapshots are deterministic across machines; if you switch to the real corpus, regenerate Q&A first.

Raw PDFs (if you choose to download them) go under `raw/` and are git-ignored.
