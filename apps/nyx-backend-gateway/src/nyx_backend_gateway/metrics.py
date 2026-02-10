from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Iterable


def _sanitize_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", " ").replace('"', '\\"')


def _format_labels(labels: dict[str, str]) -> str:
    if not labels:
        return ""
    parts = [f'{key}="{_sanitize_label(val)}"' for key, val in labels.items()]
    return "{" + ",".join(parts) + "}"


class Counter:
    def __init__(self, name: str, help_text: str, labelnames: Iterable[str] = ()) -> None:
        self.name = name
        self.help = help_text
        self.labelnames = tuple(labelnames)
        self._lock = threading.Lock()
        self._values: dict[tuple[str, ...], float] = {}

    def labels(self, **labels: str) -> "CounterChild":
        return CounterChild(self, labels)

    def inc(self, amount: float = 1.0, labels: dict[str, str] | None = None) -> None:
        label_tuple = self._label_tuple(labels or {})
        with self._lock:
            self._values[label_tuple] = self._values.get(label_tuple, 0.0) + float(amount)

    def _label_tuple(self, labels: dict[str, str]) -> tuple[str, ...]:
        if set(labels.keys()) != set(self.labelnames):
            raise ValueError(f"labels must include {self.labelnames}")
        return tuple(labels[name] for name in self.labelnames)

    def render(self) -> str:
        lines = [f"# HELP {self.name} {self.help}", f"# TYPE {self.name} counter"]
        with self._lock:
            for label_tuple, value in sorted(self._values.items()):
                label_map = dict(zip(self.labelnames, label_tuple))
                lines.append(f"{self.name}{_format_labels(label_map)} {value}")
        return "\n".join(lines)


class CounterChild:
    def __init__(self, metric: Counter, labels: dict[str, str]) -> None:
        self._metric = metric
        self._labels = labels

    def inc(self, amount: float = 1.0) -> None:
        self._metric.inc(amount, self._labels)


@dataclass
class HistogramValue:
    buckets: list[int]
    count: int
    total: float


class Histogram:
    def __init__(
        self,
        name: str,
        help_text: str,
        labelnames: Iterable[str] = (),
        buckets: Iterable[float] | None = None,
    ) -> None:
        self.name = name
        self.help = help_text
        self.labelnames = tuple(labelnames)
        self.buckets = sorted(set(buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10]))
        self._lock = threading.Lock()
        self._values: dict[tuple[str, ...], HistogramValue] = {}

    def labels(self, **labels: str) -> "HistogramChild":
        return HistogramChild(self, labels)

    def observe(self, value: float, labels: dict[str, str] | None = None) -> None:
        label_tuple = self._label_tuple(labels or {})
        with self._lock:
            record = self._values.get(label_tuple)
            if record is None:
                record = HistogramValue(buckets=[0 for _ in self.buckets], count=0, total=0.0)
                self._values[label_tuple] = record
            record.count += 1
            record.total += float(value)
            for idx, bucket in enumerate(self.buckets):
                if value <= bucket:
                    record.buckets[idx] += 1
        return None

    def _label_tuple(self, labels: dict[str, str]) -> tuple[str, ...]:
        if set(labels.keys()) != set(self.labelnames):
            raise ValueError(f"labels must include {self.labelnames}")
        return tuple(labels[name] for name in self.labelnames)

    def render(self) -> str:
        lines = [f"# HELP {self.name} {self.help}", f"# TYPE {self.name} histogram"]
        with self._lock:
            for label_tuple, record in sorted(self._values.items()):
                label_map = dict(zip(self.labelnames, label_tuple))
                cumulative = 0
                for bucket, count in zip(self.buckets, record.buckets):
                    cumulative += count
                    bucket_labels = dict(label_map)
                    bucket_labels["le"] = str(bucket)
                    lines.append(f"{self.name}_bucket{_format_labels(bucket_labels)} {cumulative}")
                bucket_labels = dict(label_map)
                bucket_labels["le"] = "+Inf"
                lines.append(f"{self.name}_bucket{_format_labels(bucket_labels)} {record.count}")
                lines.append(f"{self.name}_sum{_format_labels(label_map)} {record.total}")
                lines.append(f"{self.name}_count{_format_labels(label_map)} {record.count}")
        return "\n".join(lines)


class HistogramChild:
    def __init__(self, metric: Histogram, labels: dict[str, str]) -> None:
        self._metric = metric
        self._labels = labels

    def observe(self, value: float) -> None:
        self._metric.observe(value, self._labels)


REQUEST_COUNT = Counter(
    "nyx_gateway_http_requests_total",
    "Total HTTP requests handled by gateway.",
    ("method", "path", "status"),
)
REQUEST_LATENCY = Histogram(
    "nyx_gateway_http_request_latency_seconds",
    "Gateway HTTP request latency in seconds.",
    ("method", "path"),
)
REQUEST_ERRORS = Counter(
    "nyx_gateway_http_errors_total",
    "Gateway HTTP request errors by code.",
    ("method", "path", "code"),
)
DB_QUERY_SECONDS = Histogram(
    "nyx_gateway_db_query_seconds",
    "SQLite query duration in seconds.",
    ("operation",),
)
DB_QUERY_TOTAL = Counter(
    "nyx_gateway_db_query_total",
    "SQLite query count by operation.",
    ("operation",),
)
EVIDENCE_SECONDS = Histogram(
    "nyx_gateway_evidence_seconds",
    "Evidence adapter duration in seconds.",
    ("module", "action"),
)


def record_request(method: str, path: str, status: int, duration_seconds: float) -> None:
    REQUEST_COUNT.labels(method=method, path=path, status=str(status)).inc()
    REQUEST_LATENCY.labels(method=method, path=path).observe(duration_seconds)
    if status >= 400:
        REQUEST_ERRORS.labels(method=method, path=path, code=str(status)).inc()


def record_db_query(sql: str, duration_seconds: float) -> None:
    operation = (sql.strip().split(" ", 1)[0] or "OTHER").upper()
    DB_QUERY_TOTAL.labels(operation=operation).inc()
    DB_QUERY_SECONDS.labels(operation=operation).observe(duration_seconds)


def record_evidence_duration(module: str, action: str, duration_seconds: float) -> None:
    EVIDENCE_SECONDS.labels(module=module, action=action).observe(duration_seconds)


def render_metrics() -> str:
    parts = [
        REQUEST_COUNT.render(),
        REQUEST_LATENCY.render(),
        REQUEST_ERRORS.render(),
        DB_QUERY_TOTAL.render(),
        DB_QUERY_SECONDS.render(),
        EVIDENCE_SECONDS.render(),
    ]
    return "\n".join(part for part in parts if part)


def monotonic_seconds() -> float:
    return time.monotonic()
