"""Rewrite ``../<phase>/<leaf>/`` and ``../../<phase>/<leaf>/`` link targets
in ``docs/`` so they point at the mirrored pages under ``docs/leaves/``.

This is idempotent: it only touches links whose post-``..`` path starts with a
known phase directory, and never modifies image references, GitHub URLs, or
anchor-only links. Safe to re-run after every ``sync_leaves_to_docs.py``.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

PHASES = (
    "00-foundations",
    "01-rag",
    "02-indexing",
    "03-agentic-frameworks",
    "04-human-in-the-loop",
    "05-evals-and-observability",
    "06-mcp",
    "07-deployment-patterns",
)

PHASE_GROUP = "|".join(re.escape(p) for p in PHASES)

# `](<dots>/<phase>/<leaf>/[rest])`
LINK_RE = re.compile(
    rf"\]\((\.\./){{1,3}}(?P<phase>{PHASE_GROUP})/(?P<leaf>[^/)]+)/?(?P<rest>[^)]*)\)"
)

# Already-rewritten links that are missing the `index.md` suffix:
# `](leaves/<phase>/<leaf>/)` or `](../leaves/<phase>/<leaf>/)`.
ALREADY_REWRITTEN_RE = re.compile(
    rf"\]\((?P<prefix>(\.\./)*leaves/)(?P<phase>{PHASE_GROUP})/(?P<leaf>[^/)]+)/\)"
)

# Phase-folder-only links: `](<dots>/<phase>/)` (no leaf segment)
PHASE_ONLY_RE = re.compile(
    rf"\]\((\.\./){{1,3}}(?P<phase>{PHASE_GROUP})/\)"
)

# `shared/` or `benchmarks/` package links — keep external (GitHub).
GH_BASE = "https://github.com/vinay199129/agentic-ai-engineering/tree/main"
EXTERNAL_PKGS = ("shared", "benchmarks", "scripts", "tests")
EXTERNAL_RE = re.compile(
    rf"\]\((\.\./){{1,3}}(?P<pkg>{'|'.join(EXTERNAL_PKGS)})/?(?P<rest>[^)]*)\)"
)

# Sibling-repo links: `../../<repo-name>/...` for the two deep-dive repos.
SIBLING_REPOS = ("production-rag-pipeline", "multi-agent-research-system")
SIBLING_RE = re.compile(
    rf"\]\((\.\./){{1,3}}(?P<repo>{'|'.join(SIBLING_REPOS)})/?(?P<rest>[^)]*)\)"
)


def _rewrite(text: str, depth: int) -> tuple[str, int]:
    prefix = "../" * depth + "leaves/"

    def _sub(m: re.Match[str]) -> str:
        phase = m.group("phase")
        leaf = m.group("leaf")
        rest = m.group("rest") or ""
        if rest and not rest.startswith(("#", "?")):
            rest = ""
        anchor = rest if rest.startswith("#") else ""
        return f"]({prefix}{phase}/{leaf}/index.md{anchor})"

    def _phase_sub(m: re.Match[str]) -> str:
        phase = m.group("phase")
        return f"]({prefix}{phase}/index.md)"

    def _external_sub(m: re.Match[str]) -> str:
        pkg = m.group("pkg")
        rest = m.group("rest") or ""
        return f"]({GH_BASE}/{pkg}/{rest})"

    def _sibling_sub(m: re.Match[str]) -> str:
        repo = m.group("repo")
        rest = m.group("rest") or ""
        # The two deep-dive repos live under the same GitHub user.
        return f"](https://github.com/vinay199129/{repo}/tree/main/{rest})"

    new_text, n_leaf = LINK_RE.subn(_sub, text)
    new_text, n_phase = PHASE_ONLY_RE.subn(_phase_sub, new_text)
    new_text, n_ext = EXTERNAL_RE.subn(_external_sub, new_text)
    new_text, n_sib = SIBLING_RE.subn(_sibling_sub, new_text)

    def _suffix(m: re.Match[str]) -> str:
        return f"]({m.group('prefix')}{m.group('phase')}/{m.group('leaf')}/index.md)"

    new_text, n_suffix = ALREADY_REWRITTEN_RE.subn(_suffix, new_text)
    return new_text, n_leaf + n_phase + n_ext + n_sib + n_suffix


def main() -> None:
    n_files = 0
    n_links = 0
    for path in DOCS.rglob("*.md"):
        rel = path.relative_to(DOCS)
        # Skip the auto-generated mirror itself.
        if rel.parts and rel.parts[0] == "leaves":
            continue
        depth = len(rel.parts) - 1
        text = path.read_text(encoding="utf-8")
        new_text, n = _rewrite(text, depth)
        if n:
            path.write_text(new_text, encoding="utf-8")
            n_files += 1
            n_links += n
            print(f"  rewrote {n:>3} link(s) in {rel.as_posix()}")
    print(f"Rewrote {n_links} leaf links across {n_files} files.")


if __name__ == "__main__":
    main()
