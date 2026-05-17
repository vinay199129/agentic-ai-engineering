!!! info "`07-deployment-patterns/01-streamlit-demo-template`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/your-handle/agentic-ai-engineering/tree/main/07-deployment-patterns/01-streamlit-demo-template)

**Headline metrics:** _no headline metric_

# Streamlit demo template — a reusable shell for any agent

**Problem:** Every demo wants the same plumbing: a chat-style UI, sidebar settings, a question history, a way to surface intermediate tool calls and to render the final answer with citations. Hand-rolling this for each notebook is wasteful. A small **template** that any leaf can drop in saves dozens of LOC per demo and lands a consistent UX.

**What you'll learn:**
- The minimal Streamlit chat skeleton (`st.chat_message`, `st.session_state`) every demo needs.
- How to *inject* a solver — `app.py` is generic; you call `run(solve_fn=...)` from a sibling script for each demo.
- The "tool trace" panel: expanders that lazily reveal what the agent searched and what it found.
- Why Streamlit is the right tool here (10s to ship) and the *wrong* tool past ~50 daily users (rebuilds re-execute the whole script).

**When to use it:** Internal demos, recruiter walkthroughs, hackathons, HF Spaces.

**When NOT to use it:** External / multi-user / latency-sensitive products — reach for Next.js + Vercel AI SDK (see leaf 04) or a proper React app.

## Run it

```powershell
uv run streamlit run 07-deployment-patterns/01-streamlit-demo-template/app.py
```

CI/offline:

```powershell
uv run python 07-deployment-patterns/01-streamlit-demo-template/eval.py
```

## Key results

The eval imports `app.py`, asserts the public surface (`run`, `solve_demo`,
`render_message`), constructs the session-state dict the app expects, runs
the offline `solve_demo` against the canonical questions, and verifies
each response carries an answer + a non-empty trace. Tracked metrics:
`module_import_ok`, `public_surface_complete`, `demo_solve_success_rate`,
`avg_trace_steps`.

## References

- [Streamlit chat docs](https://docs.streamlit.io/develop/concepts/architecture/widget-behavior)
- [Hugging Face Spaces — Streamlit](https://huggingface.co/docs/hub/spaces-sdks-streamlit)
