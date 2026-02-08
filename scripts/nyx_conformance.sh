#!/usr/bin/env bash
set -euo pipefail

SEED="${SEED:-123}"
RUN_ID="${RUN_ID:-conformance}"
BASE_URL="${BASE_URL:-http://127.0.0.1:8091}"

echo "--- Conformance: Unit Tests ---"
python -m unittest packages.l0-identity.test.identity_test
python -m unittest discover -s apps/nyx-backend-gateway/test -p "*_test.py"

echo "--- Conformance: Deterministic Replay Flow ---"
bash scripts/nyx_verify_all.sh --seed "$SEED" --run-id "$RUN_ID" --base-url "$BASE_URL"

echo "--- Conformance: Proof Packaging ---"
bash scripts/nyx_pack_proof_artifacts.sh

if [[ -f "release_artifacts/SHA256SUMS.txt" ]]; then
  echo "--- Conformance: Artifact Checksums ---"
  (cd release_artifacts && sha256sum -c SHA256SUMS.txt)
fi

echo "Conformance OK"
