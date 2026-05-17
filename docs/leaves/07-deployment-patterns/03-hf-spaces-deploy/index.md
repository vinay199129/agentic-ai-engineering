!!! info "`07-deployment-patterns/03-hf-spaces-deploy`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/your-handle/agentic-ai-engineering/tree/main/07-deployment-patterns/03-hf-spaces-deploy)

**Headline metrics:** _no headline metric_

# HF Spaces deploy — CI-driven push to a public demo

**Problem:** Recruiters want to *click and try*, not clone-and-run. Hugging Face Spaces gives you a free public URL, but the manual "git push to the Space remote" workflow rots — credentials expire, branches drift, you forget. Wiring it to GitHub Actions makes the deploy *invisible*: every merge to `main` republishes the demo.

**What you'll learn:**
- The minimal **Space front-matter** that turns a folder into a working Streamlit Space (`sdk: streamlit`, `python_version`, `app_file`, hardware).
- A reusable **GitHub Actions workflow** that pushes the `space/` subfolder to a Space remote on every push to `main`.
- How to scope the **`HF_TOKEN`** secret with the *write* permission only — never owner.
- Why you want `pinned: false` and a `short_description` (they affect Spaces search ranking).

**When to use it:** Public demos for the portfolio.

**When NOT to use it:** Anything with PII, paid keys, or strict latency needs — Spaces' free CPU is unforgiving and sleeps after inactivity.

## What's in here

- `space/README.md` — the Space's own README *with the front-matter HF expects*. Push this to the Space repo.
- `space/app.py` — re-uses the Streamlit template from leaf 01.
- `space/requirements.txt` — minimal pinned deps for the Space runtime.
- `workflow.yml` — copy into `.github/workflows/deploy-hf-space.yml` in your repo.

## Run it

```powershell
# Validate everything offline:
uv run python 07-deployment-patterns/03-hf-spaces-deploy/eval.py

# Manual deploy (one-time bootstrap):
huggingface-cli upload <username>/<space-name> 07-deployment-patterns/03-hf-spaces-deploy/space . --repo-type=space
```

After that, every push to `main` republishes via `workflow.yml`.

## Key results

The eval parses the Space README front-matter, checks the required keys
exist with sane values (`sdk`, `app_file`, `python_version`), parses
`requirements.txt`, and lints `workflow.yml` for the right
`actions/checkout@` + `huggingface_hub` upload step. Tracked metrics:
`frontmatter_complete`, `requirements_parses`, `workflow_uses_official_actions`,
`secret_scope_documented`.

## References

- [HF Spaces config reference](https://huggingface.co/docs/hub/spaces-config-reference)
- [`huggingface-cli upload`](https://huggingface.co/docs/huggingface_hub/guides/cli)
