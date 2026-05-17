"""Structural eval for the HF Space payload.

Parses ``space/README.md`` front-matter (HF's contract), validates the
required keys, checks ``space/app.py`` exists, parses ``requirements.txt``,
and lints ``workflow.yml`` for the deploy-time conventions.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve()
for _p in (_HERE.parent, *_HERE.parents):
    if (_p / "shared").exists() and (_p / "pyproject.toml").exists():
        sys.path.insert(0, str(_p))
        os.chdir(_p)
        break

try:
    import yaml
except Exception as exc:  # pragma: no cover
    print("pyyaml missing. Run `uv sync --group deployment`.", file=sys.stderr)
    raise SystemExit(1) from exc


REQUIRED_FRONTMATTER = {
    "title",
    "emoji",
    "colorFrom",
    "colorTo",
    "sdk",
    "sdk_version",
    "app_file",
}


def _parse_frontmatter(text: str) -> dict[str, Any]:
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    return yaml.safe_load(match.group(1)) or {}


def main() -> None:
    base = Path(__file__).parent
    fm = _parse_frontmatter((base / "space" / "README.md").read_text(encoding="utf-8"))
    frontmatter_complete = REQUIRED_FRONTMATTER.issubset(set(fm.keys()))

    app_exists = (base / "space" / "app.py").exists()

    reqs_text = (base / "space" / "requirements.txt").read_text(encoding="utf-8")
    requirements = [
        ln.strip() for ln in reqs_text.splitlines() if ln.strip() and not ln.startswith("#")
    ]
    requirements_parses = all(
        re.match(r"^[a-zA-Z0-9_\-\[\]]+([<>=!~].+)?$", r) for r in requirements
    )

    workflow_path = base / "workflow.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    deploy_steps = workflow.get("jobs", {}).get("deploy", {}).get("steps", [])
    uses_checkout = any("actions/checkout@" in (s.get("uses") or "") for s in deploy_steps)
    uses_huggingface_upload = any(
        "huggingface-cli upload" in (s.get("run") or "") for s in deploy_steps
    )
    uses_secret_token = "secrets.HF_TOKEN" in workflow_path.read_text(encoding="utf-8")

    snapshot = {
        "technique": "hf-spaces-deploy",
        "version": "0.1.0",
        "dataset": "space-config",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "averages": {
                "frontmatter_complete": float(frontmatter_complete),
                "app_file_present": float(app_exists),
                "requirements_parses": float(bool(requirements) and requirements_parses),
                "workflow_uses_official_actions": float(uses_checkout),
                "workflow_uploads_to_space": float(uses_huggingface_upload),
                "secret_scope_documented": float(uses_secret_token),
            },
            "frontmatter": fm,
            "requirements": requirements,
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot["metrics"]["averages"], indent=2))


if __name__ == "__main__":
    main()
