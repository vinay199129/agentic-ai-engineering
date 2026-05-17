"""Reusable Streamlit demo shell.

Generic chat UI with a tool-trace panel. Demos plug in by passing a
``solve_fn`` to :func:`run`. The default ``solve_demo`` uses the in-repo
MCP corpus agent so the page is functional out of the box without API keys.
"""

from __future__ import annotations

import importlib
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

# Repo bootstrap so the same script works from any cwd.
_HERE = Path(__file__).resolve()
for _p in (_HERE.parent, *_HERE.parents):
    if (_p / "shared").exists() and (_p / "pyproject.toml").exists():
        sys.path.insert(0, str(_p))
        sys.path.insert(0, str(_p / "06-mcp"))
        break

os.environ.setdefault("LLM_CACHE_ONLY", "1")

SolveFn = Callable[[str], dict[str, Any]]


def solve_demo(question: str) -> dict[str, Any]:
    """Default solver: drives the in-repo MCP agent. Reproducible offline."""
    mcp_core = importlib.import_module("mcp_core")
    server = mcp_core.build_corpus_server(with_resources=False, with_prompts=False)
    client = mcp_core.Client(transport=mcp_core.InProcessTransport(server))
    client.initialize()
    return mcp_core.mcp_agent_solve(client, question)


def render_message(role: str, content: str) -> dict[str, str]:
    """Pure function so the eval can verify it without a Streamlit context."""
    return {"role": role, "content": content}


def _trace_lines(trace: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for step in trace:
        if step.get("role") == "tool_call":
            lines.append(f"- **{step.get('name')}** ← `{step.get('args')}`")
        elif step.get("role") == "tool_result":
            preview = str(step.get("output"))[:140].replace("\n", " ")
            lines.append(f"  - result: `{preview}`")
        else:
            lines.append(f"- {step.get('role')}: {step.get('content', '')[:140]}")
    return lines


def run(*, solve_fn: SolveFn | None = None, title: str = "Agentic demo") -> None:
    """Render the Streamlit app. Call this from your `streamlit run` entrypoint."""
    import streamlit as st  # imported lazily so `eval.py` can import this module

    solve = solve_fn or solve_demo

    st.set_page_config(page_title=title, page_icon="🤖", layout="wide")
    st.title(title)

    with st.sidebar:
        st.markdown("### Settings")
        st.caption(
            "This demo runs offline using the in-repo corpus + MCP agent. "
            "Swap `solve_fn` for your own solver to drive a real model."
        )
        if st.button("Clear chat"):
            st.session_state.pop("messages", None)
            st.session_state.pop("traces", None)
            st.rerun()

    if "messages" not in st.session_state:
        st.session_state["messages"] = []
        st.session_state["traces"] = []

    for msg, trace in zip(
        st.session_state["messages"], st.session_state["traces"] + [None], strict=False
    ):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if trace:
                with st.expander("Tool trace"):
                    st.markdown("\n".join(_trace_lines(trace)))

    question = st.chat_input("Ask a question…")
    if question:
        st.session_state["messages"].append(render_message("user", question))
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                result = solve(question)
            answer = str(result.get("answer", ""))
            st.markdown(answer)
            with st.expander("Tool trace"):
                st.markdown("\n".join(_trace_lines(result.get("trace", []))))
        st.session_state["messages"].append(render_message("assistant", answer))
        st.session_state["traces"].append(result.get("trace", []))


if __name__ == "__main__":
    run()
