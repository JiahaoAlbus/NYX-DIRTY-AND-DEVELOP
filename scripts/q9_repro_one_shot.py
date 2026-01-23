#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, text=True)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = repo_root / "apps" / "nyx-backend-gateway" / "repro"

    _run([sys.executable, "-m", "compileall", "packages/l0-identity/src"])
    _run([sys.executable, "scripts/nyx_run_all_unittests.py"])

    sys.path.insert(0, str(repo_root / "apps" / "nyx-backend" / "src"))
    sys.path.insert(0, str(repo_root / "apps" / "nyx-backend-gateway" / "src"))

    from nyx_backend.evidence import build_export_zip  # noqa: E402
    from nyx_backend_gateway.gateway import execute_run  # noqa: E402

    if "NYX_TESTNET_FEE_ADDRESS" not in os.environ:
        os.environ["NYX_TESTNET_FEE_ADDRESS"] = "testnet-fee-address"

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    seed = 123
    cases = [
        ("exchange", "route_swap", {"asset_in": "asset-a", "asset_out": "asset-b", "amount": 5, "min_out": 3}, "q9-exchange-123"),
        ("chat", "message_event", {"channel": "general", "message": "hello"}, "q9-chat-123"),
        ("marketplace", "listing_publish", {"sku": "sku-1", "title": "Item One", "price": 10}, "q9-market-123"),
        ("entertainment", "state_step", {"item_id": "ent-001", "mode": "pulse", "step": 1}, "q9-ent-123"),
    ]

    print("Q9 one-shot evidence run")
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir) / "runs"
        db_path = Path(tmpdir) / "gateway.db"
        for module, action, payload, run_id in cases:
            result = execute_run(
                seed=seed,
                run_id=run_id,
                module=module,
                action=action,
                payload=payload,
                db_path=db_path,
                run_root=base_dir,
            )
            export_bytes = build_export_zip(run_id, base_dir=base_dir)
            export_path = output_dir / f"{run_id}.zip"
            export_path.write_bytes(export_bytes)
            export_hash = _sha256_bytes(export_bytes)
            receipt_prefix = result.receipt_hashes[0][:12] if result.receipt_hashes else ""
            print(
                f"{module}:{action} state_hash={result.state_hash[:12]} "
                f"receipt_hash={receipt_prefix} replay_ok={result.replay_ok} export_sha256={export_hash[:12]}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
