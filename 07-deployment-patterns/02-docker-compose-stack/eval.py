"""Structural eval for the compose stack.

Parses ``compose.yaml`` and asserts the topology the README documents:

* All four required services are present with sensible images.
* Every service exposes a port (so the docs can reach them).
* Stateful services define a healthcheck.
* ``api`` depends on Postgres/Redis with ``condition: service_healthy``.
"""

from __future__ import annotations

import json
import os
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


REQUIRED_SERVICES: dict[str, dict[str, Any]] = {
    "api": {"image_substring": "python"},
    "postgres": {"image_substring": "pgvector"},
    "redis": {"image_substring": "redis"},
    "langfuse": {"image_substring": "langfuse"},
}


def main() -> None:
    compose_path = Path(__file__).parent / "compose.yaml"
    parsed = True
    try:
        data: dict[str, Any] = yaml.safe_load(compose_path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        parsed = False
        data = {}

    services: dict[str, dict[str, Any]] = data.get("services", {}) if parsed else {}

    present = sum(name in services for name in REQUIRED_SERVICES)
    image_matches = 0
    healthcheck_count = 0
    port_count = 0
    for name, spec in REQUIRED_SERVICES.items():
        svc = services.get(name, {})
        image = str(svc.get("image", ""))
        if spec["image_substring"] in image:
            image_matches += 1
        if "healthcheck" in svc:
            healthcheck_count += 1
        if svc.get("ports"):
            port_count += 1

    api_depends = services.get("api", {}).get("depends_on", {})
    healthy_deps = 0
    if isinstance(api_depends, dict):
        for dep in ("postgres", "redis"):
            spec = api_depends.get(dep, {})
            if isinstance(spec, dict) and spec.get("condition") == "service_healthy":
                healthy_deps += 1

    volumes = data.get("volumes", {}) if parsed else {}
    snapshot = {
        "technique": "docker-compose-stack",
        "version": "0.1.0",
        "dataset": "compose.yaml",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "averages": {
                "yaml_parses": float(parsed),
                "required_services_present": round(present / len(REQUIRED_SERVICES), 4),
                "image_match_rate": round(image_matches / len(REQUIRED_SERVICES), 4),
                "healthcheck_coverage": round(healthcheck_count / len(REQUIRED_SERVICES), 4),
                "depends_on_uses_health_condition": round(healthy_deps / 2, 4),
                "exposed_ports_coverage": round(port_count / len(REQUIRED_SERVICES), 4),
            },
            "service_names": sorted(services.keys()),
            "named_volumes": sorted(volumes.keys()) if isinstance(volumes, dict) else [],
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot["metrics"]["averages"], indent=2))


if __name__ == "__main__":
    main()
