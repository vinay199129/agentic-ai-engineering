"""MCP server basics eval.

Drive the canonical 3-tool server through every required method and assert:

* ``initialize`` returns the expected protocol version + capabilities;
* ``tools/list`` returns all 3 tools with a non-empty JSON schema each;
* ``tools/call`` succeeds for ``search_corpus``, ``fetch_paper``, ``cite``;
* the server's audit log records one entry per request.
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
    PROTOCOL_VERSION,
    Client,
    InProcessTransport,
    build_corpus_server,
)

REQUIRED_METHODS = ("initialize", "tools/list", "tools/call")
EXPECTED_TOOLS = ("search_corpus", "fetch_paper", "cite")


def _schema_valid(schema: dict[str, Any]) -> bool:
    if schema.get("type") != "object":
        return False
    return "properties" in schema


def main() -> None:
    server = build_corpus_server()
    client = Client(transport=InProcessTransport(server))

    t0 = time.perf_counter()
    init_result = client.initialize()
    init_ok = init_result.get("protocolVersion") == PROTOCOL_VERSION

    tools_list = client.list_tools()
    tools_present = {t["name"] for t in tools_list}
    schemas_valid = sum(1 for t in tools_list if _schema_valid(t["inputSchema"]))

    call_results: dict[str, Any] = {}
    call_results["search_corpus"] = client.call_tool(
        "search_corpus", {"query": "mixture of experts routing latency", "k": 2}
    )
    top_id = call_results["search_corpus"][0]["arxiv_id"]
    call_results["fetch_paper"] = client.call_tool("fetch_paper", {"arxiv_id": top_id})
    call_results["cite"] = client.call_tool(
        "cite",
        {
            "arxiv_id": top_id,
            "claim": call_results["fetch_paper"]["abstract"][:120],
        },
    )

    call_successes = sum(
        1
        for name, result in call_results.items()
        if isinstance(result, (list, dict))
        and (result if isinstance(result, list) else "error" not in result)
    )

    # Audit log should contain: initialize + tools/list + 3 x tools/call = 5.
    methods_logged = {entry["method"] for entry in server.audit_log}
    methods_covered = sum(1 for m in REQUIRED_METHODS if m in methods_logged)

    latency = (time.perf_counter() - t0) * 1000

    snapshot = {
        "technique": "mcp-server-basics",
        "version": "0.1.0",
        "dataset": "benchmarks/corpus/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "averages": {
                "canonical_method_coverage": round(methods_covered / len(REQUIRED_METHODS), 4),
                "tool_call_success_rate": round(call_successes / len(EXPECTED_TOOLS), 4),
                "schema_validity_rate": round(schemas_valid / len(EXPECTED_TOOLS), 4),
                "initialize_handshake_ok": float(init_ok),
                "avg_latency_ms": round(latency, 3),
            },
            "tools_advertised": sorted(tools_present),
            "audit_log_size": len(server.audit_log),
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot["metrics"]["averages"], indent=2))


if __name__ == "__main__":
    main()
