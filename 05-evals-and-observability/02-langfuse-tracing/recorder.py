"""In-memory trace recorder shaped like ``langfuse.Langfuse``.

Drop-in for notebooks that want to demonstrate trace structure without a
running Langfuse server. The names and parent-chain semantics match the real
client so swapping to the real one is a one-line import change.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Span:
    name: str
    span_id: str
    parent_id: str | None
    trace_id: str
    start_ts: float
    end_ts: float | None = None
    input: Any = None
    output: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)
    scores: list[Score] = field(default_factory=list)

    @property
    def duration_ms(self) -> float:
        if self.end_ts is None:
            return 0.0
        return (self.end_ts - self.start_ts) * 1000


@dataclass
class Score:
    name: str
    value: float | bool | str
    comment: str | None = None


class _SpanContext:
    def __init__(self, tracer: InMemoryTracer, span: Span):
        self._tracer = tracer
        self.span = span

    def update(self, *, input: Any = None, output: Any = None, **metadata: Any) -> None:
        if input is not None:
            self.span.input = input
        if output is not None:
            self.span.output = output
        for k, v in metadata.items():
            self.span.metadata[k] = v

    def score(self, name: str, value: float | bool | str, comment: str | None = None) -> None:
        self.span.scores.append(Score(name=name, value=value, comment=comment))

    def end(self) -> None:
        self.span.end_ts = time.perf_counter()
        self._tracer._active = self._prev_active

    def __enter__(self) -> _SpanContext:
        self._prev_active = self._tracer._active
        self._tracer._active = self
        return self

    def __exit__(self, exc_type: type[BaseException] | None, *_: Any) -> None:
        if self.span.end_ts is None:
            self.span.end_ts = time.perf_counter()
        self._tracer._active = self._prev_active


class InMemoryTracer:
    """Spec-compatible-ish stand-in for ``langfuse.Langfuse`` used in notebooks/CI."""

    def __init__(self) -> None:
        self._active: _SpanContext | None = None
        self.spans: list[Span] = []
        self.traces: dict[str, list[Span]] = {}

    def trace(self, name: str, **metadata: Any) -> _SpanContext:
        return self.span(name, parent=None, trace_root=True, **metadata)

    def span(
        self,
        name: str,
        *,
        parent: _SpanContext | None = None,
        trace_root: bool = False,
        **metadata: Any,
    ) -> _SpanContext:
        parent_id: str | None
        trace_id: str
        if trace_root or self._active is None:
            trace_id = uuid.uuid4().hex
            parent_id = None
        else:
            parent_id = self._active.span.span_id
            trace_id = self._active.span.trace_id
        span = Span(
            name=name,
            span_id=uuid.uuid4().hex,
            parent_id=parent_id,
            trace_id=trace_id,
            start_ts=time.perf_counter(),
            metadata=dict(metadata),
        )
        self.spans.append(span)
        self.traces.setdefault(trace_id, []).append(span)
        return _SpanContext(self, span)

    def flush(self) -> None:  # parity with the real client
        return None


__all__ = ["InMemoryTracer", "Score", "Span"]
