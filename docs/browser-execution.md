# Can these notebooks run in the browser?

!!! tip "Try it now — JupyterLite is built"
    The hub ships a **live, in-browser** notebook environment alongside this
    documentation. Once GitHub Pages is published, it will live at
    <a href="lite/index.html"><code>/lite/</code></a>.

    Locally, after `uv run python scripts/build_jupyterlite.py`, open
    `site/lite/lab/index.html` in your browser. 39 from-scratch leaves
    + the LLM-response cache + the shared modules are bundled — **no API
    keys, no install**.

Short answer: **the from-scratch leaves can; the framework leaves
mostly cannot.** Here is the honest breakdown and the path for each.

## Three browser-execution options ranked

| Option | What runs | Setup cost | Cold-start | Honest verdict |
|---|---|---:|---:|---|
| **JupyterLite** (Pyodide / WASM) | Pure-Python + NumPy + a few scientific libs | One-off `jupyter lite build` + GH Pages publish | ~5–10 s | Best fit for our **from-scratch** leaves |
| **mybinder.org** | Full Python with any pip deps | A `binder/requirements.txt` + a button | 30–120 s | Best fit for the **framework / heavy-dep** leaves |
| **Google Colab** | Full Python | An "Open in Colab" badge per notebook | 5–15 s | Works for everything except docker-compose leaves |

## What works in JupyterLite (Pyodide) today

Pyodide ships **numpy, scikit-learn, scipy, pandas, pydantic** and
stdlib. Anything that lives inside those bounds can run in the
browser with zero install. The hub's from-scratch leaves are
deliberately within those bounds:

| Leaf | Runs in JupyterLite? | Why |
|---|:---:|---|
| `00-foundations/01-structured-outputs` | ✅ | Uses cached LLM responses via `shared/llm.py` cache-only mode |
| `00-foundations/02-function-calling` | ✅ | Same |
| `00-foundations/03-streaming-patterns` | ✅ | Pure-Python async generators |
| `00-foundations/04-prompt-patterns` | ✅ | Cached responses; pure stdlib orchestration |
| `01-rag/00-naive-rag` | ✅ | Uses `shared/embedders.hash_embed` (numpy only) |
| `01-rag/03-hybrid-search` | ✅ | BM25 from scratch + dense from scratch |
| `01-rag/04-reranking` | ✅ | Re-ranker call goes through cache |
| `01-rag/05-query-transformation` | ✅ | Cached LLM calls |
| `01-rag/06-self-rag` | ✅ | Cached |
| `01-rag/07-corrective-rag` | ✅ | Cached |
| `01-rag/08-agentic-rag` | ✅ | Cached |
| `01-rag/09-graph-rag` | ✅ | `networkx` is in Pyodide; community detection via the python-louvain fallback |
| `01-rag/11-long-context-rag` | ✅ | Cached |
| `01-rag/12-comparison-bench` | ✅ | Pure-Python aggregator over committed snapshots |
| `02-indexing/00-vector-db-comparison` | ✅ | All implementations are NumPy |
| `02-indexing/01-hnsw-deep-dive` | ✅ | NumPy + stdlib |
| `02-indexing/02-ivf-pq-quantization` | ✅ | NumPy + stdlib |
| `02-indexing/03-bm25-and-hybrid` | ✅ | Pure Python |
| `02-indexing/04-knowledge-graph-index` | ✅ | `networkx` |
| `02-indexing/05-summary-tree-index` | ✅ | Cached LLM calls + pure tree code |
| `02-indexing/06-colbert-late-interaction` | ✅ | NumPy MaxSim |
| `02-indexing/07-incremental-indexing` | ✅ | NumPy |
| `03-agentic-frameworks/00-react-from-scratch` | ✅ | The whole point — no framework dep |
| `04-human-in-the-loop/00-interrupt-and-resume` | ✅ | `hitl.py` is pure stdlib + numpy |
| `04-human-in-the-loop/01-approval-gates` | ✅ | Same |
| `04-human-in-the-loop/02-edit-state` | ✅ | Same |
| `04-human-in-the-loop/03-time-travel-debug` | ✅ | Same |
| `04-human-in-the-loop/04-streaming-with-intervention` | ✅ | Same |
| `04-human-in-the-loop/05-async-hitl-via-queue` | ✅ | Same — in-memory queue |
| `05-evals-and-observability/00-ragas-rag-eval` | ✅ | From-scratch metrics |
| `05-evals-and-observability/01-ragas-agent-eval` | ✅ | Same |
| `05-evals-and-observability/03-llm-as-judge` | ✅ | Cached judge calls |
| `05-evals-and-observability/04-synthetic-eval-data` | ✅ | Cached generation |
| `05-evals-and-observability/05-regression-suite` | ✅ | Snapshot diffing — pure stdlib |
| `05-evals-and-observability/06-cost-and-latency-bench` | ✅ | Pure timing + token math |
| `06-mcp/00-mcp-server-basics` | ✅ | `mcp_core.py` is stdlib only |
| `06-mcp/01-mcp-client-in-agent` | ✅ | Same |
| `06-mcp/02-mcp-with-resources` | ✅ | Same |
| `06-mcp/03-custom-mcp-for-internal-api` | ✅ | Same |

**That's ~38 of 55 notebooks runnable in the browser with zero install.**

## What does *not* work in JupyterLite

These leaves need C-extension / GPU / heavy native deps that Pyodide
doesn't ship. Use mybinder or Colab.

| Leaf | Why it doesn't fit | Where to run |
|---|---|---|
| `01-rag/01-chunking-strategies` (uses `tiktoken`) | C extension | mybinder or Colab |
| `01-rag/02-embedding-comparison` | `sentence-transformers` is large | Colab (free GPU) |
| `01-rag/10-multimodal-rag` | Image models + vision LLMs | Colab |
| `03-agentic-frameworks/01-langgraph` | `langgraph` not in Pyodide | mybinder |
| `03-agentic-frameworks/02-pydantic-ai` | `pydantic-ai` install | mybinder |
| `03-agentic-frameworks/03-crewai` | `crewai` install | mybinder |
| `03-agentic-frameworks/04-microsoft-agent-framework` | `agent-framework` install | mybinder |
| `03-agentic-frameworks/05-openai-agents-sdk` | `openai-agents` install | mybinder |
| `03-agentic-frameworks/06-smolagents` | `smolagents` install | mybinder |
| `03-agentic-frameworks/07-framework-comparison` | imports all of the above | mybinder |
| `05-evals-and-observability/02-langfuse-tracing` | Langfuse server expected | local docker compose |
| `07-deployment-patterns/00-fastapi-streaming-agent` | FastAPI server | local |
| `07-deployment-patterns/01-streamlit-demo-template` | Streamlit server | local or HF Space |
| `07-deployment-patterns/02-docker-compose-stack` | Docker | local |
| `07-deployment-patterns/03-hf-spaces-deploy` | HF Spaces | the published Space |
| `07-deployment-patterns/04-ts-vercel-ai-sdk-chat` | Node + Next.js | local or Vercel preview |

## How to publish JupyterLite for this hub (one-off)

Add a `jupyterlite/` config + a GitHub Action. Below is a complete
recipe; we have **not** committed it yet because the user controls
the gh-pages branch story.

1. Add to `pyproject.toml` `[dependency-groups]`:
   ```toml
   jupyterlite = [
     "jupyterlite-core>=0.4",
     "jupyterlite-pyodide-kernel>=0.4",
     "jupyterlab>=4.2",
   ]
   ```
2. Create `jupyterlite.json`:
   ```json
   {
     "jupyter-lite-schema-version": 0,
     "jupyter-config-data": {
       "appName": "agentic-ai-engineering — try it in your browser"
     }
   }
   ```
3. Build locally:
   ```bash
   uv sync --group jupyterlite
   uv run jupyter lite build \
     --contents 00-foundations \
     --contents 01-rag \
     --contents 02-indexing \
     --contents 03-agentic-frameworks/00-react-from-scratch \
     --contents 04-human-in-the-loop \
     --contents 05-evals-and-observability \
     --contents 06-mcp \
     --contents shared \
     --contents benchmarks/golden-qa \
     --contents .llm-cache \
     --output-dir site-lite
   ```
4. Publish `site-lite/` alongside the MkDocs site via the existing
   `gh-pages` workflow. Add an "Open in JupyterLite" badge to each
   leaf README in the ✅ table above, pointing at:
   `https://<your-handle>.github.io/agentic-ai-engineering/lite/lab/?path=<leaf>/notebook.ipynb`

## How to publish a Binder badge (per-notebook)

The repo already has the data + lockfile shape Binder wants. Add at
the top of any framework-leaf README:

```markdown
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/<handle>/agentic-ai-engineering/HEAD?labpath=03-agentic-frameworks/01-langgraph/notebook.ipynb)
```

Binder will:
- Detect `pyproject.toml`,
- Install all dependency groups (slow first time, then cached),
- Drop the user into JupyterLab with the notebook open.

## Recommended path for this repo

1. **Tomorrow:** publish JupyterLite for the from-scratch leaves —
   ~38 notebooks become a one-click experience for visitors. Highest
   leverage piece of polish remaining.
2. **Later:** add Binder badges to the framework leaves so the heavier
   notebooks have a path too.
3. **Optional:** Colab badges for `01-rag/02-embedding-comparison`
   and `01-rag/10-multimodal-rag` since those benefit from the GPU.

The from-scratch story (`docs/from-scratch.md`) and the JupyterLite
story compound: a visitor lands on the GraphRAG deep-dive, opens
the notebook in the browser **without installing anything**, and the
notebook runs against committed cached LLM responses. That's the soft-
launch demo.
