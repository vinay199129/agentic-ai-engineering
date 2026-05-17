"""Build a JupyterLite site that runs the from-scratch leaves in-browser.

Pyodide ships numpy + pydantic + stdlib, which is the entire dependency
surface of the hub's from-scratch implementations (`shared/`, `06-mcp/mcp_core.py`,
`04-human-in-the-loop/hitl.py`, the indexing leaves, the evals leaves,
the foundations leaves, and `00-react-from-scratch`).

This script:

1. Stages a ``site-lite/contents/`` directory with only the leaves that are
   known to work under Pyodide (see ``BROWSER_SAFE`` below).
2. Copies the shared Python packages (``shared/``) and the LLM-response
   cache (``.llm-cache/``) so notebooks resolve imports + cached calls.
3. Runs ``jupyter lite build`` to emit a static site under ``site/lite/``
   so it lands as a sub-path of the MkDocs site at ``/lite/``.

Usage:
    uv sync --group jupyterlite --group rag --group indexing
    uv run python scripts/build_jupyterlite.py
    # Output: site/lite/  (publish alongside MkDocs site/)
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LITE_OUT = ROOT / "site" / "lite"
STAGE = ROOT / "build" / "jupyterlite"
CONTENTS = STAGE / "contents"

# Leaves whose notebook + eval.py rely only on stdlib + numpy + pydantic +
# scikit-learn + pandas + networkx (all in Pyodide). Verified by reading
# the imports of each leaf's eval.py during the dashboard work.
BROWSER_SAFE: tuple[str, ...] = (
    "00-foundations/01-structured-outputs",
    "00-foundations/02-function-calling",
    "00-foundations/03-streaming-patterns",
    "00-foundations/04-prompt-patterns",
    "01-rag/00-naive-rag",
    "01-rag/03-hybrid-search",
    "01-rag/04-reranking",
    "01-rag/05-query-transformation",
    "01-rag/06-self-rag",
    "01-rag/07-corrective-rag",
    "01-rag/08-agentic-rag",
    "01-rag/09-graph-rag",
    "01-rag/11-long-context-rag",
    "01-rag/12-comparison-bench",
    "02-indexing/00-vector-db-comparison",
    "02-indexing/01-hnsw-deep-dive",
    "02-indexing/02-ivf-pq-quantization",
    "02-indexing/03-bm25-and-hybrid",
    "02-indexing/04-knowledge-graph-index",
    "02-indexing/05-summary-tree-index",
    "02-indexing/06-colbert-late-interaction",
    "02-indexing/07-incremental-indexing",
    "03-agentic-frameworks/00-react-from-scratch",
    "04-human-in-the-loop/00-interrupt-and-resume",
    "04-human-in-the-loop/01-approval-gates",
    "04-human-in-the-loop/02-edit-state",
    "04-human-in-the-loop/03-time-travel-debug",
    "04-human-in-the-loop/04-streaming-with-intervention",
    "04-human-in-the-loop/05-async-hitl-via-queue",
    "05-evals-and-observability/00-ragas-rag-eval",
    "05-evals-and-observability/01-ragas-agent-eval",
    "05-evals-and-observability/03-llm-as-judge",
    "05-evals-and-observability/04-synthetic-eval-data",
    "05-evals-and-observability/05-regression-suite",
    "05-evals-and-observability/06-cost-and-latency-bench",
    "06-mcp/00-mcp-server-basics",
    "06-mcp/01-mcp-client-in-agent",
    "06-mcp/02-mcp-with-resources",
    "06-mcp/03-custom-mcp-for-internal-api",
)


def _copy_tree(src: Path, dst: Path, *, ignore: tuple[str, ...] = ()) -> None:
    if not src.exists():
        return
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name in ignore or (item.name.startswith(".") and item.name != ".llm-cache"):
            continue
        target = dst / item.name
        if item.is_dir():
            _copy_tree(item, target, ignore=ignore)
        else:
            shutil.copy2(item, target)


def _stage_contents() -> None:
    if STAGE.exists():
        shutil.rmtree(STAGE)
    CONTENTS.mkdir(parents=True)

    # 1. Shared packages — every leaf imports from these.
    for shared_pkg in ("shared", "benchmarks"):
        src = ROOT / shared_pkg
        if src.exists():
            _copy_tree(src, CONTENTS / shared_pkg, ignore=("__pycache__", "tests"))

    # 2. Phase-shared helpers.
    for helper in (
        "04-human-in-the-loop/hitl.py",
        "06-mcp/mcp_core.py",
        "03-agentic-frameworks/task.py",
    ):
        src = ROOT / helper
        if src.exists():
            dst = CONTENTS / helper
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    # 3. LLM cache — lets `LLM_CACHE_ONLY=1` calls succeed offline.
    cache_src = ROOT / ".llm-cache"
    if cache_src.exists():
        _copy_tree(cache_src, CONTENTS / ".llm-cache")

    # 4. Each browser-safe leaf (notebook + eval.py + README + snapshot).
    for leaf in BROWSER_SAFE:
        src_dir = ROOT / leaf
        if not src_dir.exists():
            print(f"  skip (missing): {leaf}")
            continue
        dst_dir = CONTENTS / leaf
        dst_dir.mkdir(parents=True, exist_ok=True)
        for item in src_dir.iterdir():
            if item.name in {"__pycache__", "tests"} or item.name.startswith("."):
                continue
            if item.is_file():
                shutil.copy2(item, dst_dir / item.name)
            else:
                _copy_tree(item, dst_dir / item.name, ignore=("__pycache__",))

    # 5. Browser-friendly README at the lite-site root.
    (CONTENTS / "README.md").write_text(_root_readme(), encoding="utf-8")
    print(f"Staged {len(BROWSER_SAFE)} browser-safe leaves into {CONTENTS}")


def _root_readme() -> str:
    return (
        "# agentic-ai-engineering — try it in your browser\n"
        "\n"
        "Welcome. You are running JupyterLite (Python + numpy + scikit-learn +\n"
        "pydantic + networkx, all compiled to WebAssembly). Every notebook below\n"
        "executes **in this tab**, against the committed LLM-response cache. No\n"
        "API keys required. No installation.\n"
        "\n"
        "## Where to start\n"
        "\n"
        "- `01-rag/00-naive-rag/notebook.ipynb` — minimal RAG baseline\n"
        "- `02-indexing/01-hnsw-deep-dive/notebook.ipynb` — HNSW built from scratch in NumPy\n"
        "- `03-agentic-frameworks/00-react-from-scratch/notebook.ipynb` — the ReAct loop with no framework\n"
        "- `04-human-in-the-loop/00-interrupt-and-resume/notebook.ipynb` — mini-LangGraph with interrupts\n"
        "- `06-mcp/00-mcp-server-basics/notebook.ipynb` — an in-process MCP server\n"
        "\n"
        "## What does *not* work here\n"
        "\n"
        "Framework leaves (LangGraph, CrewAI, Pydantic AI, MS Agent Framework,\n"
        "OpenAI Agents SDK, Smolagents) need real installs and are not bundled.\n"
        "Use the Binder badges in their READMEs on GitHub instead.\n"
        "\n"
        "Full repo: https://github.com/your-handle/agentic-ai-engineering\n"
    )


def _build() -> None:
    LITE_OUT.parent.mkdir(parents=True, exist_ok=True)
    if LITE_OUT.exists():
        shutil.rmtree(LITE_OUT)
    # JupyterLite refuses to serve dotfiles unless explicitly allowed.
    # `.llm-cache/` is exactly what we need to ship for cache-only mode.
    config_path = STAGE / "jupyter_lite_config.json"
    config_path.write_text(
        '{"LiteBuildConfig": {"contents": ["'
        + str(CONTENTS).replace("\\", "/")
        + '"]}, "ContentsManager": {"allow_hidden": true}}\n',
        encoding="utf-8",
    )
    cmd = [
        sys.executable,
        "-m",
        "jupyter",
        "lite",
        "build",
        "--config",
        str(config_path),
        "--contents",
        str(CONTENTS),
        "--output-dir",
        str(LITE_OUT),
    ]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=STAGE)


def main() -> None:
    print("[1/2] staging browser-safe contents…")
    _stage_contents()
    print("[2/2] building JupyterLite site…")
    _build()
    print(f"\nDone. Open: {LITE_OUT}/index.html")


if __name__ == "__main__":
    main()
