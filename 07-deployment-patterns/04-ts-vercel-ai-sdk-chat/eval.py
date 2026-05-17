"""Structural eval for the TS chat scaffold.

We don't run the JS toolchain in CI; we verify the project shape:

* ``package.json`` parses + has required deps and scripts.
* App Router files exist at the expected paths.
* The API route declares ``runtime = "edge"`` (needed for Vercel SSE).
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

_HERE = Path(__file__).resolve()
for _p in (_HERE.parent, *_HERE.parents):
    if (_p / "shared").exists() and (_p / "pyproject.toml").exists():
        sys.path.insert(0, str(_p))
        os.chdir(_p)
        break


REQUIRED_DEPS = {"ai", "next", "react", "react-dom"}
REQUIRED_SCRIPTS = {"dev", "build", "lint", "typecheck"}
REQUIRED_FILES = {
    "src/app/layout.tsx",
    "src/app/page.tsx",
    "src/app/api/chat/route.ts",
    "tsconfig.json",
}


def main() -> None:
    base = Path(__file__).parent

    pkg_parses = True
    try:
        pkg = json.loads((base / "package.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        pkg_parses = False
        pkg = {}

    deps = set(pkg.get("dependencies", {}).keys()) if pkg_parses else set()
    scripts = set(pkg.get("scripts", {}).keys()) if pkg_parses else set()
    deps_present = REQUIRED_DEPS.issubset(deps)
    scripts_present = REQUIRED_SCRIPTS.issubset(scripts)

    files_present = sum((base / rel).exists() for rel in REQUIRED_FILES)

    route_text = (base / "src" / "app" / "api" / "chat" / "route.ts").read_text(encoding="utf-8")
    edge_runtime = 'runtime = "edge"' in route_text
    proxies_backend = "/agent/stream" in route_text

    page_text = (base / "src" / "app" / "page.tsx").read_text(encoding="utf-8")
    handles_interrupt = "interrupt" in page_text and "/agent/resume" in page_text

    snapshot = {
        "technique": "ts-vercel-ai-sdk-chat",
        "version": "0.1.0",
        "dataset": "scaffold",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "averages": {
                "package_json_parses": float(pkg_parses),
                "required_deps_present": float(deps_present),
                "required_scripts_present": float(scripts_present),
                "app_router_files_present": round(files_present / len(REQUIRED_FILES), 4),
                "edge_runtime_declared": float(edge_runtime),
                "backend_proxy_wired": float(proxies_backend),
                "interrupt_handled_in_ui": float(handles_interrupt),
            },
            "deps": sorted(deps),
            "scripts": sorted(scripts),
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot["metrics"]["averages"], indent=2))


if __name__ == "__main__":
    main()
