"""Resources-and-prompts eval.

Server is built with ``with_resources=True, with_prompts=True``. The eval:

* Calls ``resources/list``, then ``resources/read`` on each advertised URI;
* Calls ``prompts/list`` then ``prompts/get`` with sample arguments;
* Asserts URI uniqueness and prompt structural validity.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve()
for _p in (_HERE.parent, *_HERE.parents):
    if (_p / "shared").exists() and (_p / "pyproject.toml").exists():
        sys.path.insert(0, str(_p))
        os.chdir(_p)
        break

sys.path.insert(0, str(_HERE.parent.parent))

if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
    os.environ.setdefault("LLM_CACHE_ONLY", "1")

from mcp_core import (  # noqa: E402
    Client,
    InProcessTransport,
    build_corpus_server,
)


def _prompt_valid(messages: list[dict[str, Any]]) -> bool:
    if len(messages) < 2:
        return False
    roles = {m.get("role") for m in messages}
    if not {"system", "user"}.issubset(roles):
        return False
    for m in messages:
        c = m.get("content")
        if not isinstance(c, dict) or c.get("type") != "text" or not c.get("text"):
            return False
    return True


def main() -> None:
    server = build_corpus_server(with_resources=True, with_prompts=True)
    client = Client(transport=InProcessTransport(server))
    client.initialize()

    t0 = time.perf_counter()
    resources = client.list_resources()
    uris = [r["uri"] for r in resources]
    read_success = 0
    for r in resources:
        text = client.read_resource(r["uri"])
        if text and r["uri"].startswith("arxiv://"):
            read_success += 1

    prompts = client.list_prompts()
    sample_question = "What does RA-MoE do?"
    rendered = client.get_prompt("research", {"question": sample_question})

    n_resources = len(resources)
    latency = (time.perf_counter() - t0) * 1000

    snapshot = {
        "technique": "mcp-with-resources",
        "version": "0.1.0",
        "dataset": "benchmarks/corpus/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "averages": {
                "resource_read_success_rate": round(read_success / max(n_resources, 1), 4),
                "resource_uri_uniqueness": round(len(set(uris)) / max(n_resources, 1), 4),
                "prompt_render_validity": float(_prompt_valid(rendered)),
                "avg_latency_ms": round(latency, 3),
            },
            "counts": {
                "resources": n_resources,
                "prompts": len(prompts),
                "tools": len(client.list_tools()),
            },
            "sample_rendered_prompt": rendered,
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot["metrics"]["averages"], indent=2))


if __name__ == "__main__":
    main()
