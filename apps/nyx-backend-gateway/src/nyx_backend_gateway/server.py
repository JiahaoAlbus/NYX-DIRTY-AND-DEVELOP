from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from nyx_backend_gateway.env import load_env_file
from nyx_backend_gateway.gateway import GatewayError, execute_run, _run_root, _db_path
from nyx_backend_gateway.storage import create_connection, list_orders, list_trades, load_by_id


_MAX_BODY = 4096
_RATE_LIMIT = 120
_RATE_WINDOW_SECONDS = 60


class RequestLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self._limit = limit
        self._window = window_seconds
        self._state: dict[str, tuple[int, float]] = {}

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        count, start = self._state.get(key, (0, now))
        if now - start >= self._window:
            count, start = 0, now
        if count >= self._limit:
            self._state[key] = (count, start)
            return False
        self._state[key] = (count + 1, start)
        return True


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

    def _rate_limit_ok(self) -> bool:
        limiter = getattr(self.server, "rate_limiter", None)
        if limiter is None:
            return True
        client = self.client_address[0] if self.client_address else "unknown"
        return limiter.allow(client)

    def _require_run_id(self, payload: dict) -> str:
        run_id = payload.get("run_id")
        if not isinstance(run_id, str) or not run_id or isinstance(run_id, bool):
            raise GatewayError("run_id required")
        return run_id

    def _require_seed(self, payload: dict) -> int:
        seed = payload.get("seed")
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise GatewayError("seed must be int")
        return seed

    def _require_query_run_id(self, query: dict[str, list[str]]) -> str:
        run_id = (query.get("run_id") or [""])[0]
        if not run_id:
            raise GatewayError("run_id required")
        return run_id

    def do_POST(self) -> None:  # noqa: N802
        if not self._rate_limit_ok():
            self._send_text("rate limit exceeded", HTTPStatus.TOO_MANY_REQUESTS)
            return
        try:
            if self.path == "/run":
                payload = self._parse_body()
                seed = self._require_seed(payload)
                run_id = self._require_run_id(payload)
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
                        "state_hash": result.state_hash,
                        "receipt_hashes": result.receipt_hashes,
                        "replay_ok": result.replay_ok,
                    }
                )
                return
            if self.path == "/exchange/place_order":
                payload = self._parse_body()
                seed = self._require_seed(payload)
                run_id = self._require_run_id(payload)
                order_payload = payload.get("payload")
                if order_payload is None:
                    order_payload = {k: v for k, v in payload.items() if k not in {"seed", "run_id"}}
                result = execute_run(
                    seed=seed,
                    run_id=run_id,
                    module="exchange",
                    action="place_order",
                    payload=order_payload,
                )
                self._send_json(
                    {
                        "run_id": result.run_id,
                        "status": "complete",
                        "state_hash": result.state_hash,
                        "receipt_hashes": result.receipt_hashes,
                        "replay_ok": result.replay_ok,
                    }
                )
                return
            if self.path == "/exchange/cancel_order":
                payload = self._parse_body()
                seed = self._require_seed(payload)
                run_id = self._require_run_id(payload)
                cancel_payload = payload.get("payload")
                if cancel_payload is None:
                    cancel_payload = {k: v for k, v in payload.items() if k not in {"seed", "run_id"}}
                result = execute_run(
                    seed=seed,
                    run_id=run_id,
                    module="exchange",
                    action="cancel_order",
                    payload=cancel_payload,
                )
                self._send_json(
                    {
                        "run_id": result.run_id,
                        "status": "complete",
                        "state_hash": result.state_hash,
                        "receipt_hashes": result.receipt_hashes,
                        "replay_ok": result.replay_ok,
                    }
                )
                return
            self._send_text("not found", HTTPStatus.NOT_FOUND)
        except GatewayError as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def do_GET(self) -> None:  # noqa: N802
        if not self._rate_limit_ok():
            self._send_text("rate limit exceeded", HTTPStatus.TOO_MANY_REQUESTS)
            return
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == "/status":
            try:
                run_id = self._require_query_run_id(query)
                from nyx_backend.evidence import EvidenceError, load_evidence

                evidence = load_evidence(run_id, base_dir=_run_root())
                self._send_json({"status": "complete", "replay_ok": evidence.replay_ok})
            except EvidenceError as exc:
                self._send_json({"status": "error", "error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/evidence":
            try:
                run_id = self._require_query_run_id(query)
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
            try:
                run_id = self._require_query_run_id(query)
                name = (query.get("name") or [""])[0]
                from nyx_backend.evidence import EvidenceError, _safe_artifact_path

                artifact_path = _safe_artifact_path(_run_root(), run_id, name)
                data = artifact_path.read_bytes()
            except EvidenceError as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            self._send_bytes(data, "application/octet-stream")
            return
        if path == "/export.zip":
            try:
                run_id = self._require_query_run_id(query)
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
        if path == "/exchange/orders":
            try:
                conn = create_connection(_db_path())
                side = (query.get("side") or [""])[0] or None
                asset_in = (query.get("asset_in") or [""])[0] or None
                asset_out = (query.get("asset_out") or [""])[0] or None
                orders = list_orders(conn, side=side, asset_in=asset_in, asset_out=asset_out)
                conn.close()
                self._send_json({"orders": orders})
            except Exception as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/exchange/trades":
            try:
                conn = create_connection(_db_path())
                trades = list_trades(conn)
                conn.close()
                self._send_json({"trades": trades})
            except Exception as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/exchange/orderbook":
            try:
                conn = create_connection(_db_path())
                buys = list_orders(conn, side="BUY", order_by="price DESC, order_id ASC")
                sells = list_orders(conn, side="SELL", order_by="price ASC, order_id ASC")
                conn.close()
                self._send_json({"buy": buys, "sell": sells})
            except Exception as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        self._send_text("not found", HTTPStatus.NOT_FOUND)


def run_server(host: str = "0.0.0.0", port: int = 8091) -> None:
    server = ThreadingHTTPServer((host, port), GatewayHandler)
    server.rate_limiter = RequestLimiter(_RATE_LIMIT, _RATE_WINDOW_SECONDS)
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NYX backend gateway")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8091)
    parser.add_argument("--env-file", default="")
    args = parser.parse_args()
    if args.env_file:
        load_env_file(Path(args.env_file))
    run_server(host=args.host, port=args.port)
