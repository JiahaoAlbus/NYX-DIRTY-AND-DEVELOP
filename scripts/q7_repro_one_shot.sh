#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

python -m unittest discover -p "*_test.py" -v

PYTHONPATH="apps/reference-ui-backend/src:packages/e2e-private-transfer/src:packages/l2-private-ledger/src:packages/l0-zk-id/src:packages/l2-economics/src:packages/l1-chain/src:packages/wallet-kernel/src" \
  python - <<'PY'
from pathlib import Path
from nyx_reference_ui_backend.evidence import build_export_zip, run_evidence

base_dir = Path("/tmp/nyx_q7_repro")
run_id = "q7-repro-123"
payload = run_evidence(seed=123, run_id=run_id, base_dir=base_dir)
zip_bytes = build_export_zip(run_id, base_dir)
Path("/tmp/nyx_q7_repro_export.zip").write_bytes(zip_bytes)
print(
    "state_hash="
    + payload.state_hash
    + " receipt_hashes="
    + ",".join(payload.receipt_hashes)
    + " replay_ok="
    + str(payload.replay_ok)
)
PY
