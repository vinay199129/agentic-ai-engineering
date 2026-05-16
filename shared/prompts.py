"""Reusable prompt templates.

Keep these small. A leaf folder is welcome to inline its own prompt — only
promote one here once two notebooks need the same wording.
"""

from __future__ import annotations

from collections.abc import Sequence

RAG_SYSTEM = (
    "You are a precise research assistant. Answer the user's question using "
    "ONLY the provided context. If the answer is not in the context, reply "
    'exactly: "I don\'t know based on the provided context." Cite sources by '
    "their bracketed id, e.g. [doc-3]."
)


def rag_user_prompt(question: str, contexts: Sequence[tuple[str, str]]) -> str:
    """Render the user prompt for a RAG call.

    Parameters
    ----------
    question:
        The user's question, verbatim.
    contexts:
        Sequence of ``(doc_id, text)`` tuples in retrieval order.
    """
    if not contexts:
        return f"Question: {question}\n\nContext: (none)\n\nAnswer:"
    blocks = "\n\n".join(f"[{doc_id}] {text.strip()}" for doc_id, text in contexts)
    return f"Question: {question}\n\nContext:\n{blocks}\n\nAnswer:"


STRUCTURED_EXTRACTION_SYSTEM = (
    "Extract the requested fields from the user's text. Respond with ONLY a "
    "JSON object matching the provided schema. No prose, no markdown fences."
)


__all__ = ["RAG_SYSTEM", "STRUCTURED_EXTRACTION_SYSTEM", "rag_user_prompt"]
