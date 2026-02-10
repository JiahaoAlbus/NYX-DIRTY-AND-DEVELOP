from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from nyx_backend.evidence import (
    EvidenceError,
    build_export_zip,
    list_runs,
    load_evidence,
    run_evidence,
)
from nyx_backend import metrics, tracing


class GatewayHandler(BaseHTTPRequestHandler):
    server_version = "NYXGateway/1.0"
    _response_status: int | None = None

    def send_response(self, code: int, message: str | None = None) -> None:  # type: ignore[override]
        self._response_status = code
        super().send_response(code, message)

    def _record_metrics(self, method: str, start_time: float) -> None:
        try:
            path = urlparse(self.path).path
        except Exception:
            path = self.path
        status = self._response_status or HTTPStatus.INTERNAL_SERVER_ERROR
        metrics.record_request(method, path, int(status), metrics.monotonic_seconds() - start_time)

    def handle_one_request(self) -> None:  # type: ignore[override]
        start = metrics.monotonic_seconds()
        self._response_status = None
        try:
            super().handle_one_request()
        finally:
            if self.command:
                self._record_metrics(self.command, start)

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_text(self, payload: str, status: HTTPStatus) -> None:
        data = payload.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_bytes(self, data: bytes, content_type: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_metrics(self) -> None:
        payload = metrics.render_metrics().encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _parse_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        body = self.rfile.read(length)
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            raise EvidenceError("invalid json")
        if not isinstance(payload, dict):
            raise EvidenceError("payload must be object")
        return payload

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/metrics":
            self._send_metrics()
            return
        if self.path != "/run":
            self._send_text("not found", HTTPStatus.NOT_FOUND)
            return
        try:
            payload = self._parse_body()
            seed = payload.get("seed")
            run_id = payload.get("run_id")
            module = payload.get("module")
            action = payload.get("action")
            extra = payload.get("payload")
            start = metrics.monotonic_seconds()
            with tracing.start_span(
                "backend.evidence.run",
                {
                    "nyx.module": module,
                    "nyx.action": action,
                    "nyx.run_id": run_id,
                },
            ):
                evidence = run_evidence(seed=seed, run_id=run_id, module=module, action=action, payload=extra)
            metrics.record_evidence_duration(str(module), str(action), metrics.monotonic_seconds() - start)
            self._send_json({"run_id": run_id, "status": "complete", "replay_ok": evidence.replay_ok})
        except EvidenceError as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == "/status":
            run_id = (query.get("run_id") or [""])[0]
            try:
                evidence = load_evidence(run_id)
                self._send_json({"status": "complete", "replay_ok": evidence.replay_ok})
            except EvidenceError as exc:
                self._send_json({"status": "error", "error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/evidence":
            run_id = (query.get("run_id") or [""])[0]
            try:
                evidence = load_evidence(run_id)
            except EvidenceError as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            payload = {
                "protocol_anchor": evidence.protocol_anchor,
                "inputs": evidence.inputs,
                "outputs": evidence.outputs,
                "receipt_hashes": evidence.receipt_hashes,
                "state_hash": evidence.state_hash,
                "replay_ok": evidence.replay_ok,
                "stdout": evidence.stdout,
            }
            self._send_json(payload)
            return
        if path == "/artifact":
            run_id = (query.get("run_id") or [""])[0]
            name = (query.get("name") or [""])[0]
            try:
                artifact_path = _artifact_path(run_id, name)
                data = artifact_path.read_bytes()
            except EvidenceError as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            self._send_bytes(data, "application/octet-stream")
            return
        if path == "/export.zip":
            run_id = (query.get("run_id") or [""])[0]
            try:
                data = build_export_zip(run_id)
            except EvidenceError as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            self._send_bytes(data, "application/zip")
            return
        if path == "/list":
            records = list_runs()
            payload = [
                {"run_id": record.run_id, "status": record.status}
                for record in records
            ]
            self._send_json({"runs": payload})
            return
        if path == "/metrics":
            self._send_metrics()
            return
        self._send_text("not found", HTTPStatus.NOT_FOUND)


def _artifact_path(run_id: str, name: str) -> Path:
    from nyx_backend.evidence import _run_root, _safe_artifact_path

    root = _run_root()
    return _safe_artifact_path(root, run_id, name)


def run_server(host: str = "0.0.0.0", port: int = 8090) -> None:
    tracing.init_tracing("nyx-backend")
    server = ThreadingHTTPServer((host, port), GatewayHandler)
    server.serve_forever()


if __name__ == "__main__":
    run_server()
