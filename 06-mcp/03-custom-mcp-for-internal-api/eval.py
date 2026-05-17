"""Custom-MCP-for-internal-API eval.

Wraps a deterministic in-process "weather API" with two MCP tools:

* ``get_forecast(city, units)`` — trims the verbose upstream payload to
  ``{city, temp_c, conditions, updated_at}``.
* ``set_alert(city, threshold_c)`` — destructive; subject to a rate limit.

The eval drives both tools with valid + invalid inputs and quantifies how
much smaller the wrapped payloads are vs upstream.
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
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
    Server,
)

# ---------------------------------------------------------------------------
# Simulated upstream "internal weather API" — verbose, enum-heavy, what real
# internal services look like before LLM-friendliness gets retrofitted.
# ---------------------------------------------------------------------------

UPSTREAM_FIXTURES: dict[str, dict[str, Any]] = {
    "Bengaluru": {
        "city_id": 11423,
        "city_canonical_name": "Bengaluru",
        "region_code": "IN-KA",
        "tz_offset_minutes": 330,
        "current": {
            "temp": {"unit": "celsius", "value": 28.4, "fahrenheit_value": 83.1},
            "conditions_enum": "PARTLY_CLOUDY",
            "wind": {"speed_kph": 12.6, "direction_deg": 220},
            "humidity_pct": 71,
            "pressure_hpa": 1011,
            "uv_index": 5,
        },
        "updated_at_iso": "2026-05-17T07:00:00Z",
        "raw_provider_payload": {"id": "p-991", "version": "v3.2"},
    },
    "Seattle": {
        "city_id": 56329,
        "city_canonical_name": "Seattle",
        "region_code": "US-WA",
        "tz_offset_minutes": -480,
        "current": {
            "temp": {"unit": "celsius", "value": 12.1, "fahrenheit_value": 53.8},
            "conditions_enum": "LIGHT_RAIN",
            "wind": {"speed_kph": 18.2, "direction_deg": 200},
            "humidity_pct": 88,
            "pressure_hpa": 1006,
            "uv_index": 2,
        },
        "updated_at_iso": "2026-05-17T07:00:00Z",
        "raw_provider_payload": {"id": "p-114", "version": "v3.2"},
    },
}

CONDITION_HUMANIZE: dict[str, str] = {
    "PARTLY_CLOUDY": "partly cloudy",
    "LIGHT_RAIN": "light rain",
    "CLEAR": "clear",
    "HEAVY_RAIN": "heavy rain",
    "OVERCAST": "overcast",
}


@dataclass
class RateLimiter:
    max_calls: int
    window_s: float
    calls: list[float] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.calls = []

    def allow(self) -> bool:
        now = time.perf_counter()
        self.calls = [t for t in self.calls if now - t < self.window_s]
        if len(self.calls) >= self.max_calls:
            return False
        self.calls.append(now)
        return True


def build_weather_server() -> tuple[Server, RateLimiter, dict[str, int]]:
    """Wrap the upstream fixtures behind two MCP tools."""
    rate = RateLimiter(max_calls=2, window_s=60.0)
    upstream_bytes: dict[str, int] = {"forecast": 0, "alerts": 0}
    server = Server(name="internal-weather", version="0.1.0")

    def get_forecast(city: str, units: str = "celsius") -> dict[str, Any]:
        if units not in ("celsius", "fahrenheit"):
            return {"error": f"units must be celsius|fahrenheit, got {units!r}"}
        if city not in UPSTREAM_FIXTURES:
            return {"error": f"unknown city {city!r}"}
        raw = UPSTREAM_FIXTURES[city]
        upstream_bytes["forecast"] += len(json.dumps(raw, default=str))
        temp = raw["current"]["temp"]
        temp_value = temp["value"] if units == "celsius" else temp["fahrenheit_value"]
        return {
            "city": raw["city_canonical_name"],
            "temp": round(float(temp_value), 1),
            "units": units,
            "conditions": CONDITION_HUMANIZE.get(
                raw["current"]["conditions_enum"], raw["current"]["conditions_enum"].lower()
            ),
            "updated_at": raw["updated_at_iso"],
        }

    def set_alert(city: str, threshold_c: float) -> dict[str, Any]:
        if not rate.allow():
            return {"error": "rate_limited", "retry_after_s": 60}
        if city not in UPSTREAM_FIXTURES:
            return {"error": f"unknown city {city!r}"}
        upstream_bytes["alerts"] += 256
        return {
            "city": city,
            "threshold_c": threshold_c,
            "alert_id": f"alert-{city.lower()}-{int(threshold_c)}",
            "active": True,
        }

    server.add_tool(
        "get_forecast",
        "Current weather for a city. Returns city, temp, units, conditions, updated_at.",
        {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "city name; e.g. Bengaluru"},
                "units": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "default": "celsius",
                },
            },
            "required": ["city"],
        },
        get_forecast,
    )
    server.add_tool(
        "set_alert",
        "Create a temperature-threshold alert. Rate-limited; safe to retry on rate_limited.",
        {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "threshold_c": {"type": "number"},
            },
            "required": ["city", "threshold_c"],
        },
        set_alert,
    )
    return server, rate, upstream_bytes


def main() -> None:
    server, _rate, upstream_bytes = build_weather_server()
    client = Client(transport=InProcessTransport(server))
    client.initialize()

    t0 = time.perf_counter()
    calls: list[tuple[str, dict[str, Any]]] = [
        ("get_forecast", {"city": "Bengaluru"}),
        ("get_forecast", {"city": "Seattle", "units": "fahrenheit"}),
        ("get_forecast", {"city": "Atlantis"}),  # error path
        ("get_forecast", {"city": "Bengaluru", "units": "kelvin"}),  # bad units
    ]
    forecast_results: list[dict[str, Any]] = []
    wrapped_bytes = 0
    successes = 0
    for name, args in calls:
        out = client.call_tool(name, args)
        forecast_results.append({"args": args, "result": out})
        wrapped_bytes += len(json.dumps(out, default=str))
        if isinstance(out, dict) and "error" not in out:
            successes += 1

    # set_alert: 3 calls, max 2 allowed -> exactly 1 should be rate-limited.
    alert_calls = [("Bengaluru", 35.0), ("Seattle", 25.0), ("Bengaluru", 36.0)]
    alert_results: list[dict[str, Any]] = []
    rate_limited = 0
    for city, threshold in alert_calls:
        out = client.call_tool("set_alert", {"city": city, "threshold_c": threshold})
        alert_results.append({"args": {"city": city, "threshold_c": threshold}, "result": out})
        if isinstance(out, dict) and out.get("error") == "rate_limited":
            rate_limited += 1

    latency = (time.perf_counter() - t0) * 1000

    forecast_upstream = upstream_bytes["forecast"]
    trim_ratio = 1.0 - (wrapped_bytes / max(forecast_upstream, 1)) if forecast_upstream else 0.0

    snapshot = {
        "technique": "custom-mcp-for-internal-api",
        "version": "0.1.0",
        "dataset": "fixtures/weather",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "averages": {
                "wrap_call_success_rate": round(successes / 2, 4),  # 2 happy paths
                "payload_trim_ratio": round(max(trim_ratio, 0.0), 4),
                "rate_limit_enforcement_rate": round(rate_limited / 1, 4),  # exactly 1 expected
                "avg_latency_ms": round(latency, 3),
            },
            "forecast_calls": forecast_results,
            "alert_calls": alert_results,
            "upstream_bytes": upstream_bytes,
            "wrapped_bytes": wrapped_bytes,
        },
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot["metrics"]["averages"], indent=2))


if __name__ == "__main__":
    main()
