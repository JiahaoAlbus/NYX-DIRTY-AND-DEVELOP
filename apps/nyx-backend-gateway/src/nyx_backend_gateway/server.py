from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from nyx_backend_gateway.gateway import GatewayError, execute_run, _run_root


_MAX_BODY = 4096


class GatewayHandler(BaseHTTPRequestHandler):
    server_version = "NYXGateway/2.0"

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

    def _parse_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        if length > _MAX_BODY:
            raise GatewayError("payload too large")
        body = self.rfile.read(length)
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            raise GatewayError("invalid json")
        if not isinstance(payload, dict):
            raise GatewayError("payload must be object")
        return payload

    def do_POST(self) -> None:  # noqa: N802
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
            result = execute_run(
                seed=seed,
                run_id=run_id,
                module=module,
                action=action,
                payload=extra,
            )
            self._send_json(
                {
                    "run_id": result.run_id,
                    "status": "complete",
                    "replay_ok": result.replay_ok,
                }
            )
        except GatewayError as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == "/status":
            run_id = (query.get("run_id") or [""])[0]
            try:
                from nyx_backend.evidence import EvidenceError, load_evidence

                evidence = load_evidence(run_id, base_dir=_run_root())
                self._send_json({"status": "complete", "replay_ok": evidence.replay_ok})
            except EvidenceError as exc:
                self._send_json({"status": "error", "error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/evidence":
            run_id = (query.get("run_id") or [""])[0]
            try:
                from nyx_backend.evidence import EvidenceError, load_evidence

                evidence = load_evidence(run_id, base_dir=_run_root())
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
                from nyx_backend.evidence import EvidenceError, _safe_artifact_path

                artifact_path = _safe_artifact_path(_run_root(), run_id, name)
                data = artifact_path.read_bytes()
            except EvidenceError as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            self._send_bytes(data, "application/octet-stream")
            return
        if path == "/export.zip":
            run_id = (query.get("run_id") or [""])[0]
            try:
                from nyx_backend.evidence import EvidenceError, build_export_zip

                data = build_export_zip(run_id, base_dir=_run_root())
            except EvidenceError as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            self._send_bytes(data, "application/zip")
            return
        if path == "/list":
            from nyx_backend.evidence import list_runs

            records = list_runs(base_dir=_run_root())
            payload = [{"run_id": record.run_id, "status": record.status} for record in records]
            self._send_json({"runs": payload})
            return
        self._send_text("not found", HTTPStatus.NOT_FOUND)


def run_server(host: str = "0.0.0.0", port: int = 8091) -> None:
    server = ThreadingHTTPServer((host, port), GatewayHandler)
    server.serve_forever()


if __name__ == "__main__":
    run_server()
