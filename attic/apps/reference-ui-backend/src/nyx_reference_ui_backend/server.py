from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from nyx_reference_ui_backend.evidence import (
    EvidenceError,
    build_export_zip,
    list_runs,
    load_evidence,
    run_evidence,
    _safe_artifact_path,
    _sanitize_run_id,
)


class ReferenceUIHandler(BaseHTTPRequestHandler):
    server_version = "NYXReferenceUI/1.0"

    def _repo_root(self) -> Path:
        path = Path(__file__).resolve()
        for _ in range(5):
            path = path.parent
        return path

    def _static_dir(self) -> Path:
        return self._repo_root() / "apps" / "reference-ui" / "static"

    def _send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_bytes(self, data: bytes, content_type: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_text(self, text: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        return

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/run":
            self._send_text("not found", HTTPStatus.NOT_FOUND)
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            self._send_json({"error": "invalid json"}, HTTPStatus.BAD_REQUEST)
            return
        seed = payload.get("seed")
        run_id = payload.get("run_id")
        if not run_id:
            self._send_json({"error": "run_id required"}, HTTPStatus.BAD_REQUEST)
            return
        try:
            safe_run_id = _sanitize_run_id(run_id)
            run_evidence(seed=seed, run_id=safe_run_id)
        except (EvidenceError, TypeError):
            self._send_json({"error": "run failed"}, HTTPStatus.BAD_REQUEST)
            return
        response = {"run_id": safe_run_id, "status": "complete"}
        self._send_json(response)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/status":
            run_id = (query.get("run_id") or [""])[0]
            try:
                evidence = load_evidence(run_id)
            except EvidenceError:
                self._send_json({"status": "not_found", "error": "run_id not found"})
                return
            self._send_json({"status": "complete", "replay_ok": evidence.replay_ok})
            return

        if path == "/evidence":
            run_id = (query.get("run_id") or [""])[0]
            try:
                evidence = load_evidence(run_id)
            except EvidenceError:
                self._send_json({"error": "run_id not found"}, HTTPStatus.NOT_FOUND)
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
                repo_root = self._repo_root()
                runs_root = repo_root / "apps" / "reference-ui-backend" / "runs"
                artifact_path = _safe_artifact_path(runs_root, run_id, name)
            except EvidenceError:
                self._send_text("not found", HTTPStatus.NOT_FOUND)
                return
            if not artifact_path.exists():
                self._send_text("not found", HTTPStatus.NOT_FOUND)
                return
            self._send_bytes(artifact_path.read_bytes(), "application/octet-stream")
            return

        if path == "/export.zip":
            run_id = (query.get("run_id") or [""])[0]
            try:
                data = build_export_zip(run_id)
            except EvidenceError:
                self._send_text("not found", HTTPStatus.NOT_FOUND)
                return
            self._send_bytes(data, "application/zip")
            return

        if path == "/list":
            records = [record.__dict__ for record in list_runs()]
            self._send_json({"runs": records})
            return

        if path == "/":
            path = "/home"

        static_dir = self._static_dir()
        if path.startswith("/assets/"):
            file_path = static_dir / path.lstrip("/")
        elif path.startswith("/js/"):
            file_path = static_dir / path.lstrip("/")
        else:
            file_path = static_dir / (path.lstrip("/") + ".html")
        if not file_path.exists():
            self._send_text("not found", HTTPStatus.NOT_FOUND)
            return
        content_type = "text/html; charset=utf-8"
        if file_path.suffix == ".css":
            content_type = "text/css; charset=utf-8"
        if file_path.suffix == ".js":
            content_type = "application/javascript; charset=utf-8"
        self._send_bytes(file_path.read_bytes(), content_type)


def run_server(host: str = "0.0.0.0", port: int = 8080) -> None:
    server = ThreadingHTTPServer((host, port), ReferenceUIHandler)
    server.serve_forever()


if __name__ == "__main__":
    run_server()
