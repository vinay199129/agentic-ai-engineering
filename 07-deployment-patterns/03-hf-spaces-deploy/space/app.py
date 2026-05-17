"""Streamlit Space entrypoint.

Imports the in-repo demo template if available; otherwise renders a minimal
"hello" page so the Space always boots green.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE = REPO_ROOT / "07-deployment-patterns" / "01-streamlit-demo-template"
MCP = REPO_ROOT / "06-mcp"
if TEMPLATE.exists():
    sys.path.insert(0, str(TEMPLATE))
if MCP.exists():
    sys.path.insert(0, str(MCP))
sys.path.insert(0, str(REPO_ROOT))

try:
    from app import run  # type: ignore

    run(title="Agentic AI Engineering — Demo")
except Exception:  # pragma: no cover - fallback for HF Spaces image
    import streamlit as st

    st.title("Agentic AI Engineering — Demo")
    st.info(
        "The demo template wasn't bundled in this Space. "
        "Visit the source repo: "
        "https://github.com/vinay199129/agentic-ai-engineering"
    )
