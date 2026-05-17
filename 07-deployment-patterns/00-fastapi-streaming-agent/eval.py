"""End-to-end SSE + resume eval using a real uvicorn server.

Spawns the app on an ephemeral port (no TestClient — it buffers SSE), opens
a streaming GET, observes the interrupt frame, POSTs the decision, then
drains the rest of the SSE stream.
"""

from __future__ import annotations

import json
import os
import socket
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from threading import Event, Thread
from typing import Any

_HERE = Path(__file__).resolve()
for _p in (_HERE.parent, *_HERE.parents):
    if (_p / "shared").exists() and (_p / "pyproject.toml").exists():
        sys.path.insert(0, str(_p))
        os.chdir(_p)
        break

sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent.parent.parent / "04-human-in-the-loop"))

os.environ.setdefault("LLM_CACHE_ONLY", "1")

try:
    import httpx
    import uvicorn
except Exception as exc:  # pragma: no cover
    print(
        "fastapi/httpx/uvicorn not installed. Run `uv sync --group deployment` then re-run.",
        file=sys.stderr,
    )
    raise SystemExit(1) from exc

from app import THREADS, app  # type: ignore  # noqa: E402


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _parse_sse(chunks: list[str]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    pending: dict[str, str] = {}
    raw = "".join(chunks)
    for line in raw.splitlines():
        if not line.strip():
            if "data" in pending:
                try:
                    events.append(json.loads(pending["data"]))
                except json.JSONDecodeError:
                    events.append({"event": pending.get("event", "raw"), "raw": pending["data"]})
            pending = {}
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            pending[key.strip()] = value.strip()
    return events


class _UvicornServer(uvicorn.Server):
    def install_signal_handlers(self) -> None:  # type: ignore[override]
        pass  # no-op so we can run on a worker thread


def main() -> None:
    THREADS.clear()
    port = _free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = _UvicornServer(config=config)
    server_thread = Thread(target=server.run, daemon=True)
    server_thread.start()

    # Wait for server readiness.
    base = f"http://127.0.0.1:{port}"
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            r = httpx.get(f"{base}/healthz", timeout=0.5)
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(0.05)
    else:
        raise RuntimeError("server failed to start")

    thread_id = "eval-thread"
    question = "Summarise RA-MoE."

    collected: list[str] = []
    stop = Event()

    def _stream() -> None:
        try:
            with (
                httpx.Client(timeout=15) as cl,
                cl.stream(
                    "GET",
                    f"{base}/agent/stream",
                    params={"question": question, "thread_id": thread_id},
                ) as r,
            ):
                for chunk in r.iter_text():
                    collected.append(chunk)
                    if '"complete"' in chunk:
                        stop.set()
                        return
        except Exception as e:  # pragma: no cover
            collected.append(f"STREAM_ERROR: {e}")
            stop.set()

    t0 = time.perf_counter()
    th = Thread(target=_stream, daemon=True)
    th.start()

    interrupt_seen = False
    deadline = time.time() + 10
    while time.time() < deadline:
        if any("interrupt" in c for c in collected):
            interrupt_seen = True
            break
        time.sleep(0.05)

    resume_ok = False
    if interrupt_seen:
        with httpx.Client(timeout=5) as cl:
            resume_resp = cl.post(
                f"{base}/agent/resume",
                json={"thread_id": thread_id, "decision": "approve"},
            )
            resume_ok = resume_resp.status_code == 200

    stop.wait(timeout=10)
    th.join(timeout=2)
    latency = (time.perf_counter() - t0) * 1000

    server.should_exit = True
    server_thread.join(timeout=5)

    events = _parse_sse(collected)
    completed = any(e.get("event") == "complete" for e in events)
    has_node_event = any(e.get("event") == "node_complete" for e in events)

    snapshot = {
        "technique": "fastapi-streaming-agent",
        "version": "0.1.0",
        "dataset": "scenarios/single-question",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "averages": {
                "stream_frame_count": float(len(events)),
                "interrupt_observed": float(interrupt_seen),
                "resume_completes": float(resume_ok and completed),
                "node_event_present": float(has_node_event),
                "avg_latency_ms": round(latency, 3),
            },
            "events": [e.get("event") for e in events],
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot["metrics"]["averages"], indent=2))


if __name__ == "__main__":
    main()
