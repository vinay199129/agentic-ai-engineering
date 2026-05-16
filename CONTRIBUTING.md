# Contributing

This is primarily a personal portfolio, but it's structured to be contributable. PRs that add new techniques, fix bugs, or improve evaluations are welcome.

## Leaf-folder template

Every leaf folder under a topic directory follows the same shape:

```
01-rag/04-reranking/                  # example leaf
├── README.md                         # required
├── notebook.ipynb                    # required
├── app.py                            # optional — small Streamlit/Gradio demo
├── eval.py                           # required if the technique has measurable behavior
├── eval-snapshot.json                # committed; produced by eval.py
├── tests/                            # optional — pytest for reusable code
│   └── test_*.py
└── requirements.in                   # optional — extra deps beyond the topic's group
```

### `README.md` (required, ~150 words)

```markdown
# <technique name>

**Problem:** what hurts without this technique.
**What you'll learn:** 3–5 bullets.
**When to use it:** 1–2 sentences with concrete signals.
**When NOT to use it:** 1 sentence.

## Run it
…

## Key results
- (auto-pasted from eval-snapshot.json)

## References
- Paper / blog / framework docs
```

### `notebook.ipynb`

- **Markdown cells must stay in sync with code cells.** If you change the chunk size, update the markdown that explains the chunk size.
- **No API keys in cells.** Use `os.getenv("ANTHROPIC_API_KEY")`.
- **Use the shared `litellm` shim** in `shared/llm.py` so notebooks run on any provider.
- **First cell** sets `LLM_CACHE_ONLY` if running offline (CI does this automatically).
- **Last cell** writes `eval-snapshot.json` if applicable.

### `eval.py` + `eval-snapshot.json`

- `eval.py` must be runnable standalone: `uv run python eval.py`.
- It writes a JSON file with this shape:

  ```json
  {
    "technique": "reranking",
    "version": "0.1.0",
    "dataset": "benchmarks/golden-qa/v1",
    "run_id": "2026-05-17T12:00:00Z",
    "metrics": {
      "context_precision": 0.78,
      "context_recall": 0.82,
      "faithfulness": 0.91,
      "answer_relevancy": 0.85,
      "latency_p50_ms": 1240,
      "cost_per_query_usd": 0.0021
    }
  }
  ```

- CI compares your snapshot against `main`. A drop > 5% on any tracked metric fails the PR. Override with a labeled justification in the PR description if intentional.

## Conventional commits

Enforced via `pre-commit`. Use these types:

- `feat:` new technique / folder / capability
- `fix:` bug or doc fix
- `eval:` eval snapshot update only
- `docs:` README/CONTRIBUTING/docs site only
- `chore:` tooling, CI, deps
- `refactor:`, `perf:`, `test:`

Scope optional but encouraged: `feat(rag): add CRAG`.

## Adding a new technique (new leaf folder)

1. Copy the structure of the closest existing leaf as a template.
2. Add any new runtime deps to the relevant group in root `pyproject.toml`.
3. Run `uv sync --group <topic>`.
4. Build the notebook, write `eval.py`, run it, commit the snapshot.
5. Update the parent topic's `README.md` table.
6. Update the root `README.md` skills matrix if the folder demonstrates a new skill.

## Local dev

```bash
uv sync --group dev
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
uv run pytest               # all tests
uv run ruff check .         # lint
uv run mypy .               # types
uv run mkdocs serve         # local docs site at :8000
```

## Code style

- Python 3.12+, type-annotated everywhere, `mypy --strict` clean.
- Functions over classes when state isn't needed.
- Async-first for any I/O.
- Pydantic for all data shapes that cross a boundary (API, file, prompt).
