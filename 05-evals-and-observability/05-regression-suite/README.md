# Regression suite — guard every snapshot in CI

**Problem:** Without a regression check, the second-best version of your pipeline can ship without anyone noticing. The CI script `.github/scripts/diff_eval_snapshots.py` already compares snapshots between two git refs and fails the PR on > 5% drift. This leaf packages that pattern as a **library + pytest fixture** so individual leaves can opt into stricter per-metric guards.

**What you'll learn:**
- A tiny `regression` module that walks every `eval-snapshot.json` in the repo and flattens its metrics.
- A pytest fixture that compares the current snapshots against a committed `baseline.json` with a configurable tolerance.
- Direction-aware comparison (recall ↑, latency ↓) so the same tolerance applies in both directions.
- How CI's diff-vs-base-branch check (`.github/scripts/diff_eval_snapshots.py`) and this leaf's per-leaf guard *complement* each other.

**When to use this knowledge:** When a single leaf has a hard SLO ("recall must stay ≥ 0.85"); when you want to lock a specific metric in CI; when you're refactoring shared code and want a snapshot smoke test.

**When NOT to bother:** Greenfield experiments where any drift is expected. The repo-level CI check (5% tolerance, vs main) is enough for everything else.

## Run it

```powershell
uv sync --group evals
uv run jupyter lab 05-evals-and-observability/05-regression-suite/notebook.ipynb
uv run python 05-evals-and-observability/05-regression-suite/eval.py
uv run pytest 05-evals-and-observability/05-regression-suite/tests
```

## Key results

See [`eval-snapshot.json`](./eval-snapshot.json) for: total snapshots tracked, total flat metrics, breakdown of higher-is-better vs lower-is-better classifications, and the result of comparing current snapshots against the committed `baseline.json`.

## References

- `.github/scripts/diff_eval_snapshots.py` — the cross-ref check
- pytest [reusable fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- LangChain LangSmith, [Regression testing patterns](https://docs.smith.langchain.com/observability/how_to_guides/run_regression_evals)
