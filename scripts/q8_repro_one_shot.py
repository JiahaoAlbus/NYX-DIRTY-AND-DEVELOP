#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, text=True)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    runs_dir = repo_root / "apps" / "nyx-backend" / "runs"
    output_dir = repo_root / "apps" / "nyx-backend" / "repro"

    _run([sys.executable, "-m", "compileall", "packages/l0-identity/src"])
    _run([sys.executable, "scripts/nyx_run_all_unittests.py"])

    sys.path.insert(0, str(repo_root / "apps" / "nyx-backend" / "src"))
    from nyx_backend.evidence import build_export_zip, run_evidence  # noqa: E402

    if runs_dir.exists():
        shutil.rmtree(runs_dir)
    runs_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    seed = 123
    cases = [
        ("exchange", "route_swap", {"route": "basic"}, "q8-exchange-123"),
        ("chat", "message_event", {"message": "hello"}, "q8-chat-123"),
        ("marketplace", "order_intent", {"item_id": "kit-01", "quantity": 1}, "q8-market-123"),
        ("entertainment", "state_step", {"mode": "pulse", "step": 1}, "q8-ent-123"),
    ]

    print("Q8 one-shot evidence run")
    for module, action, payload, run_id in cases:
        evidence = run_evidence(
            seed=seed,
            run_id=run_id,
            module=module,
            action=action,
            payload=payload,
        )
        export_bytes = build_export_zip(run_id)
        export_path = output_dir / f"{run_id}.zip"
        export_path.write_bytes(export_bytes)
        export_hash = _sha256_bytes(export_bytes)
        receipt_prefix = evidence.receipt_hashes[0][:12] if evidence.receipt_hashes else ""
        print(
            f"{module}:{action} state_hash={evidence.state_hash[:12]} "
            f"receipt_hash={receipt_prefix} replay_ok={evidence.replay_ok} export_sha256={export_hash[:12]}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
