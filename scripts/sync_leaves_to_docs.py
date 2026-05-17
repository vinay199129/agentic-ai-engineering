"""Mirror every leaf's README.md + notebook.ipynb into ``docs/leaves/`` so
the MkDocs site actually publishes the technique content (instead of just
linking to GitHub folders that 404 on the published site).

For each leaf ``<phase>/<leaf>/``:

- copy ``README.md`` → ``docs/leaves/<phase>/<leaf>/index.md``
- copy ``notebook.ipynb`` → ``docs/leaves/<phase>/<leaf>/notebook.ipynb``
  (mkdocs-jupyter, already enabled, renders it as HTML)
- prepend a tiny banner pointing back to the GitHub source + the eval snapshot

A phase-level ``docs/leaves/<phase>/index.md`` lists every leaf in that phase,
and a top-level ``docs/leaves/index.md`` lists every phase.

Finally we emit ``docs/_nav_leaves.yml`` — a YAML fragment listing every leaf
in mkdocs ``nav:`` form. It is included into ``mkdocs.yml`` manually by
copy-pasting between the markers ``# >>> leaves >>>`` / ``# <<< leaves <<<``.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT = DOCS / "leaves"

PHASE_DIRS = (
    "00-foundations",
    "01-rag",
    "02-indexing",
    "03-agentic-frameworks",
    "04-human-in-the-loop",
    "05-evals-and-observability",
    "06-mcp",
    "07-deployment-patterns",
)

PHASE_TITLES = {
    "00-foundations": "Phase 0 — Foundations",
    "01-rag": "Phase 1 — RAG",
    "02-indexing": "Phase 2 — Indexing internals",
    "03-agentic-frameworks": "Phase 3 — Agentic frameworks",
    "04-human-in-the-loop": "Phase 4 — Human-in-the-loop",
    "05-evals-and-observability": "Phase 5 — Evals & observability",
    "06-mcp": "Phase 6 — MCP",
    "07-deployment-patterns": "Phase 7 — Deployment",
}

EVAL_KEYS_PRIORITY = (
    "tool_call_accuracy",
    "final_answer_grounded",
    "faithfulness",
    "context_recall",
    "answer_exact_match_direct",
    "schema_validity_rate",
    "canonical_method_coverage",
)


def _leaf_dirs() -> list[Path]:
    leaves: list[Path] = []
    for phase in PHASE_DIRS:
        phase_dir = ROOT / phase
        if not phase_dir.exists():
            continue
        for child in sorted(phase_dir.iterdir()):
            if child.is_dir() and (child / "README.md").exists():
                leaves.append(child)
    return leaves


def _walk_metrics(obj: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            out.update(_walk_metrics(v, key))
    elif isinstance(obj, (int, float, str, bool)) or obj is None:
        out[prefix] = obj
    return out


def _read_snapshot(leaf: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    snap_path = leaf / "eval-snapshot.json"
    if not snap_path.exists():
        return {}, {}
    try:
        data = json.loads(snap_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, {}
    return data, _walk_metrics(data.get("metrics", {}))


def _format_headlines(flat: dict[str, Any]) -> str:
    seen: set[str] = set()
    parts: list[str] = []
    for key, val in flat.items():
        short = key.split(".")[-1]
        if any(short.endswith(p) for p in EVAL_KEYS_PRIORITY):
            if short in seen:
                continue
            seen.add(short)
            if isinstance(val, float):
                val = f"{val:.3f}".rstrip("0").rstrip(".")
            parts.append(f"`{short}`={val}")
        if len(parts) >= 3:
            break
    return " · ".join(parts) if parts else "_no headline metric_"


_RELATIVE_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\((?!https?://|/)([^)]+)\)")
_RELATIVE_LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\((?!https?://|#|/)([^)]+)\)")


def _rewrite_relative_links(text: str, leaf_rel: str) -> str:
    """Rewrite README links so they still work from docs/leaves/<phase>/<leaf>/.

    - ``notebook.ipynb`` stays as-is (mirrored alongside, mkdocs-jupyter renders it).
    - Sibling leaves: ``../../06-mcp/00-mcp-server-basics/`` →
      ``../../06-mcp/00-mcp-server-basics/index.md`` (resolves to mirrored page).
    - Anything else → GitHub blob URL fallback.
    """
    gh_base = f"https://github.com/your-handle/agentic-ai-engineering/blob/main/{leaf_rel}"
    gh_raw = f"https://raw.githubusercontent.com/your-handle/agentic-ai-engineering/main/{leaf_rel}"

    # Build a regex that catches cross-leaf relative links so they resolve inside the docs site.
    phases = "|".join(
        re.escape(p)
        for p in (
            "00-foundations",
            "01-rag",
            "02-indexing",
            "03-agentic-frameworks",
            "04-human-in-the-loop",
            "05-evals-and-observability",
            "06-mcp",
            "07-deployment-patterns",
        )
    )
    cross_leaf_re = re.compile(
        rf"\]\((\.\./){{1,3}}(?P<phase>{phases})/(?P<leaf>[^/)]+)/?(?P<rest>[^)]*)\)"
    )

    def _cross(m: re.Match[str]) -> str:
        phase = m.group("phase")
        leaf_to = m.group("leaf")
        return f"](../../{phase}/{leaf_to}/index.md)"

    def _image(m: re.Match[str]) -> str:
        alt, target = m.group(1), m.group(2).strip()
        if target == "notebook.ipynb":
            return f"![{alt}]({target})"
        return f"![{alt}]({gh_raw}/{target})"

    def _link(m: re.Match[str]) -> str:
        label, target = m.group(1), m.group(2).strip()
        if target == "notebook.ipynb":
            return f"[{label}](notebook.ipynb)"
        if target.startswith("#"):
            return m.group(0)
        return f"[{label}]({gh_base}/{target})"

    # Cross-leaf links first so the generic fallback doesn't shove them out to GitHub.
    text = cross_leaf_re.sub(_cross, text)
    text = _RELATIVE_IMAGE_RE.sub(_image, text)
    text = _RELATIVE_LINK_RE.sub(_link, text)
    return text


def _write_leaf(leaf: Path) -> dict[str, Any]:
    leaf_rel = leaf.relative_to(ROOT).as_posix()
    phase = leaf_rel.split("/")[0]
    out_dir = OUT / leaf_rel
    out_dir.mkdir(parents=True, exist_ok=True)

    # README → index.md, with link rewriting + a small banner.
    readme_src = leaf / "README.md"
    body = readme_src.read_text(encoding="utf-8")
    body = _rewrite_relative_links(body, leaf_rel)

    snap_data, flat_metrics = _read_snapshot(leaf)
    headline_str = _format_headlines(flat_metrics) if flat_metrics else ""
    headline_line = f"**Headline metrics:** {headline_str}\n\n" if headline_str else ""

    notebook_link = ""
    if (leaf / "notebook.ipynb").exists():
        notebook_link = "📓 [Open the notebook](notebook.ipynb)  \n"

    banner = (
        f"!!! info \"`{leaf_rel}`\"\n"
        f"    {notebook_link}    "
        f"💻 [View source on GitHub]"
        f"(https://github.com/your-handle/agentic-ai-engineering/tree/main/{leaf_rel})\n\n"
        f"{headline_line}"
    )

    (out_dir / "index.md").write_text(banner + body, encoding="utf-8")

    # notebook.ipynb (rendered by mkdocs-jupyter)
    nb_src = leaf / "notebook.ipynb"
    if nb_src.exists():
        shutil.copy2(nb_src, out_dir / "notebook.ipynb")

    return {
        "leaf": leaf_rel,
        "phase": phase,
        "slug": leaf.name,
        "title": snap_data.get("technique", leaf.name),
        "headline": headline_str,
        "has_notebook": (leaf / "notebook.ipynb").exists(),
    }


def _write_phase_index(phase: str, leaves: list[dict[str, Any]]) -> None:
    phase_dir = OUT / phase
    phase_dir.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append(f"# {PHASE_TITLES.get(phase, phase)}")
    lines.append("")
    lines.append(f"{len(leaves)} leaves shipped in this phase. Click any leaf to read its README + run its notebook.")
    lines.append("")
    lines.append("| Leaf | Headline metrics | Notebook? |")
    lines.append("|---|---|:---:|")
    for r in leaves:
        nb = "✅" if r["has_notebook"] else "—"
        link = f"[`{r['slug']}`]({r['slug']}/index.md)"
        lines.append(f"| {link} | {r['headline'] or '—'} | {nb} |")
    lines.append("")
    (phase_dir / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_root_index(by_phase: dict[str, list[dict[str, Any]]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# All leaves")
    lines.append("")
    lines.append(
        "Every leaf of the hub repo, rendered in-browser. The notebooks are "
        "rendered statically by mkdocs-jupyter; to **execute** them in your "
        "browser, use the [JupyterLite site](../browser-execution.md)."
    )
    lines.append("")
    for phase in PHASE_DIRS:
        if phase not in by_phase:
            continue
        title = PHASE_TITLES.get(phase, phase)
        leaves = by_phase[phase]
        lines.append(f"## [{title}]({phase}/index.md)")
        lines.append("")
        for r in leaves:
            lines.append(f"- [`{r['slug']}`]({phase}/{r['slug']}/index.md) — {r['headline'] or '_no headline metric_'}")
        lines.append("")
    (OUT / "index.md").write_text("\n".join(lines), encoding="utf-8")


def _emit_nav_fragment(by_phase: dict[str, list[dict[str, Any]]]) -> str:
    lines: list[str] = ["  - All leaves:"]
    lines.append("    - Overview: leaves/index.md")
    for phase in PHASE_DIRS:
        if phase not in by_phase:
            continue
        title = PHASE_TITLES.get(phase, phase)
        lines.append(f"    - \"{title}\":")
        lines.append(f"      - Overview: leaves/{phase}/index.md")
        for r in by_phase[phase]:
            lines.append(f"      - \"{r['slug']}\":")
            lines.append(
                f"        - README: leaves/{phase}/{r['slug']}/index.md"
            )
            if r["has_notebook"]:
                lines.append(
                    f"        - Notebook: leaves/{phase}/{r['slug']}/notebook.ipynb"
                )
    fragment = "\n".join(lines) + "\n"
    (DOCS / "_nav_leaves.yml").write_text(fragment, encoding="utf-8")
    return fragment


_NAV_BEGIN = "  # >>> leaves >>>"
_NAV_END = "  # <<< leaves <<<"


def _patch_mkdocs_nav(fragment: str) -> None:
    cfg_path = ROOT / "mkdocs.yml"
    text = cfg_path.read_text(encoding="utf-8")
    block = f"{_NAV_BEGIN}\n{fragment}{_NAV_END}"
    if _NAV_BEGIN in text and _NAV_END in text:
        pattern = re.compile(
            rf"{re.escape(_NAV_BEGIN)}.*?{re.escape(_NAV_END)}",
            re.DOTALL,
        )
        text = pattern.sub(block, text)
    else:
        # First-time setup: inject right before the file ends.
        text = text.rstrip() + "\n" + block + "\n"
    cfg_path.write_text(text, encoding="utf-8")


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    leaves = _leaf_dirs()
    by_phase: dict[str, list[dict[str, Any]]] = {}
    for leaf in leaves:
        record = _write_leaf(leaf)
        by_phase.setdefault(record["phase"], []).append(record)
    for phase, recs in by_phase.items():
        _write_phase_index(phase, recs)
    _write_root_index(by_phase)
    fragment = _emit_nav_fragment(by_phase)
    _patch_mkdocs_nav(fragment)
    n_leaves = sum(len(v) for v in by_phase.values())
    print(f"Mirrored {n_leaves} leaves across {len(by_phase)} phases into docs/leaves/")
    print("Patched mkdocs.yml nav between # >>> leaves >>> / # <<< leaves <<< markers.")


if __name__ == "__main__":
    main()
