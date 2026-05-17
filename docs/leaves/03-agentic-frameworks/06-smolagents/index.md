!!! info "`03-agentic-frameworks/06-smolagents`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/your-handle/agentic-ai-engineering/tree/main/03-agentic-frameworks/06-smolagents)

**Headline metrics:** `tool_call_accuracy`=1 · `final_answer_grounded`=0.333

# smolagents — code as the action

**Problem:** Most agent frameworks emit JSON tool calls. smolagents (HuggingFace) takes a different bet: the action is **Python code**. The agent writes `cite("synth-001", "RA-MoE cuts latency by 38%")` directly, the framework runs it in a sandbox, and the next turn sees the result. Code is more expressive than JSON.

**What you'll learn:**
- `CodeAgent` — the agent emits Python; the framework executes.
- The **sandbox** layer — restricting imports, capping execution time, preventing IO.
- Where code-action wins (compositional reasoning, math, multi-step transforms) and where it doesn't (simple tool dispatch).
- HuggingFace's philosophy: small, focused frameworks over kitchen-sink ones.

**When to use it:** Reasoning-heavy agents (math, data wrangling, multi-step transforms). When your "tools" are best composed in code rather than chained one-at-a-time.

**When NOT to use it:** Strict-IO production where allowing arbitrary code is a compliance no-go (use guardrails-heavy SDKs). Simple single-tool dispatch (overkill).

## Run it

```powershell
uv sync --group frameworks
uv add smolagents
uv run jupyter lab 03-agentic-frameworks/06-smolagents/notebook.ipynb
uv run python 03-agentic-frameworks/06-smolagents/eval.py
```

CI uses the offline reference solver.

## Key results

See [`eval-snapshot.json`](https://github.com/your-handle/agentic-ai-engineering/blob/main/03-agentic-frameworks/06-smolagents/./eval-snapshot.json) for the four shared metrics on the demo set.

## What this leaf intentionally skips

- The vision-language `Tool.from_hub` pattern — see `01-rag/10-multimodal-rag/` for multimodal RAG patterns instead.
- E2B sandboxing — production deployments should use a real sandbox rather than `LocalPythonInterpreter`.

## References

- [smolagents docs](https://huggingface.co/docs/smolagents/)
- Wang et al., [Executable Code Actions Elicit Better LLM Agents](https://arxiv.org/abs/2402.01030)
- [E2B sandboxes](https://e2b.dev/)
