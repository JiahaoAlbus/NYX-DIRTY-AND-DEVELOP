#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen


REQUIRED_FIELDS = [
    "protocol_anchor",
    "inputs",
    "outputs",
    "receipt_hashes",
    "state_hash",
    "replay_ok",
    "stdout",
]


def _request_json(method: str, url: str, payload: dict | None = None) -> bytes:
    data = None
    if payload is not None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    req = Request(url, data=data, method=method)
    if payload is not None:
        req.add_header("Content-Type", "application/json")
    with urlopen(req, timeout=5) as resp:
        return resp.read()


def _get_json(url: str) -> tuple[bytes, dict]:
    raw = _request_json("GET", url)
    return raw, json.loads(raw.decode("utf-8"))


def _post_json(url: str, payload: dict) -> tuple[bytes, dict]:
    raw = _request_json("POST", url, payload)
    return raw, json.loads(raw.decode("utf-8"))


def _health_ok(base_url: str) -> bool:
    try:
        raw, payload = _get_json(f"{base_url}/healthz")
        return payload.get("ok") is True
    except Exception:
        return False


def _start_backend(repo_root: Path) -> subprocess.Popen:
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        f"{repo_root / 'apps' / 'nyx-backend-gateway' / 'src'}:{repo_root / 'apps' / 'nyx-backend' / 'src'}"
    )
    env_file = repo_root / "cswdz.env"
    if not env_file.exists():
        env_file = repo_root / ".env.example"
    cmd = [
        sys.executable,
        "-m",
        "nyx_backend_gateway.server",
        "--host",
        "127.0.0.1",
        "--port",
        "8091",
        "--env-file",
        str(env_file),
    ]
    return subprocess.Popen(cmd, env=env)


def _wait_for_port(host: str, port: int, timeout: float = 10.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def _ensure_fields(payload: dict) -> None:
    missing = [key for key in REQUIRED_FIELDS if key not in payload]
    if missing:
        raise RuntimeError(f"missing fields: {missing}")


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _record_evidence(base_url: str, run_id: str, out_dir: Path) -> None:
    ev_raw_1, ev_payload_1 = _get_json(f"{base_url}/evidence?run_id={run_id}")
    ev_raw_2, ev_payload_2 = _get_json(f"{base_url}/evidence?run_id={run_id}")
    if ev_raw_1 != ev_raw_2:
        raise RuntimeError("evidence response is not deterministic")
    _ensure_fields(ev_payload_1)

    zip_raw_1 = _request_json("GET", f"{base_url}/export.zip?run_id={run_id}")
    zip_raw_2 = _request_json("GET", f"{base_url}/export.zip?run_id={run_id}")
    if zip_raw_1 != zip_raw_2:
        raise RuntimeError("export.zip is not deterministic")

    _write_bytes(out_dir / run_id / "evidence.json", ev_raw_1)
    _write_bytes(out_dir / run_id / "export.zip", zip_raw_1)


def _resolve_out_dir(repo_root: Path, out_dir_arg: str) -> Path:
    if out_dir_arg:
        out_dir = Path(out_dir_arg).expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir
    out_dir = repo_root / "docs" / "evidence" / "smoke" / datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--run-id", default="smoke-run")
    parser.add_argument("--base-url", default="http://127.0.0.1:8091")
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    out_dir = _resolve_out_dir(repo_root, args.out_dir)

    if args.dry_run:
        _write_bytes(out_dir / "dry_run.txt", b"dry-run")
        print(f"Smoke artifacts: {out_dir}")
        return 0

    proc = None
    if not _health_ok(args.base_url):
        proc = _start_backend(repo_root)
        if not _wait_for_port("127.0.0.1", 8091):
            if proc:
                proc.terminate()
            raise SystemExit("backend failed to start")

    try:
        seed = args.seed
        run_id = args.run_id

        _post_json(
            f"{args.base_url}/wallet/faucet",
            {"seed": seed, "run_id": f"{run_id}-wallet-faucet", "payload": {"address": "wallet-alpha", "amount": 1000}},
        )
        _record_evidence(args.base_url, f"{run_id}-wallet-faucet", out_dir)

        _post_json(
            f"{args.base_url}/wallet/transfer",
            {
                "seed": seed,
                "run_id": f"{run_id}-wallet-transfer",
                "payload": {"from_address": "wallet-alpha", "to_address": "wallet-beta", "amount": 10},
            },
        )
        _record_evidence(args.base_url, f"{run_id}-wallet-transfer", out_dir)

        _post_json(
            f"{args.base_url}/exchange/place_order",
            {
                "seed": seed,
                "run_id": f"{run_id}-exchange-order",
                "payload": {
                    "side": "BUY",
                    "asset_in": "TEST",
                    "asset_out": "USDX",
                    "amount": 5,
                    "price": 10,
                },
            },
        )
        _record_evidence(args.base_url, f"{run_id}-exchange-order", out_dir)

        _post_json(
            f"{args.base_url}/chat/send",
            {
                "seed": seed,
                "run_id": f"{run_id}-chat",
                "payload": {"channel": "general", "message": "testnet-alpha"},
            },
        )
        _record_evidence(args.base_url, f"{run_id}-chat", out_dir)

        listing_resp_raw, listing_resp = _post_json(
            f"{args.base_url}/marketplace/listing",
            {
                "seed": seed,
                "run_id": f"{run_id}-market-list",
                "payload": {"sku": "kit-01", "title": "Testnet Kit", "price": 12},
            },
        )
        _record_evidence(args.base_url, f"{run_id}-market-list", out_dir)

        _, listings = _get_json(f"{args.base_url}/marketplace/listings")
        listing_id = (listings.get("listings") or [{}])[0].get("listing_id")
        if not listing_id:
            raise RuntimeError("listing_id missing")

        _post_json(
            f"{args.base_url}/marketplace/purchase",
            {
                "seed": seed,
                "run_id": f"{run_id}-market-buy",
                "payload": {"listing_id": listing_id, "qty": 1},
            },
        )
        _record_evidence(args.base_url, f"{run_id}-market-buy", out_dir)

        _post_json(
            f"{args.base_url}/entertainment/step",
            {
                "seed": seed,
                "run_id": f"{run_id}-ent",
                "payload": {"item_id": "ent-001", "mode": "pulse", "step": 1},
            },
        )
        _record_evidence(args.base_url, f"{run_id}-ent", out_dir)

        manifest = {
            "seed": seed,
            "run_id": run_id,
            "runs": sorted([p.name for p in out_dir.iterdir() if p.is_dir()]),
        }
        _write_bytes(out_dir / "manifest.json", json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    finally:
        if proc:
            proc.terminate()
            proc.wait(timeout=5)

    print(f"Smoke artifacts: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
