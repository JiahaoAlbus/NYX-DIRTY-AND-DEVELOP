from __future__ import annotations

import os
from contextlib import contextmanager, nullcontext
from typing import Iterator

_tracer = None
_initialized = False


def init_tracing(service_name: str) -> bool:
    global _initialized, _tracer
    if _initialized:
        return _tracer is not None
    _initialized = True

    enabled = os.environ.get("NYX_OTEL_ENABLED", "").lower() in {"1", "true", "yes"}
    if not enabled:
        return False
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter
    except Exception:
        return False

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    exporter = ConsoleSpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer(service_name)
    return True


@contextmanager
def start_span(name: str, attributes: dict[str, object] | None = None) -> Iterator[object]:
    if _tracer is None:
        yield None
        return
    span_cm = _tracer.start_as_current_span(name)
    with span_cm as span:
        if attributes:
            for key, value in attributes.items():
                try:
                    span.set_attribute(key, value)
                except Exception:
                    continue
        yield span


def span_context(name: str, attributes: dict[str, object] | None = None):
    if _tracer is None:
        return nullcontext()
    return start_span(name, attributes)
