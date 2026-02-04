#!/usr/bin/env bash
set -euo pipefail

# NYX Proof Artifacts Packaging Script
#
# Produces a single tar.gz bundle suitable for reviewers:
# - Key docs (gap report, parity rules, runbook, invariants, matrix)
# - Latest verify_all evidence folder under docs/evidence/
# - Checksums (SHA256SUMS.txt)

RELEASE_DIR="release_artifacts"
PROOF_DIR="${RELEASE_DIR}/proof"

last_path_file="docs/evidence/last_verify_path.txt"
if [[ ! -f "$last_path_file" ]]; then
  echo "No last verify marker found; running verify script with defaults…" >&2
  bash scripts/nyx_verify_all.sh
fi

evidence_root="$(cat "$last_path_file" 2>/dev/null || true)"
if [[ -z "$evidence_root" || ! -d "$evidence_root" ]]; then
  echo "Invalid evidence root in $last_path_file: $evidence_root" >&2
  exit 1
fi

timestamp="$(date +%Y%m%d_%H%M%S)"
bundle_name="nyx-proof-${timestamp}.tar.gz"
stage="${PROOF_DIR}/stage_${timestamp}"

mkdir -p "$stage/docs" "$stage/evidence"

copy_if_exists() {
  local path="$1"
  if [[ -f "$path" ]]; then
    cp "$path" "$stage/docs/"
  fi
}

copy_if_exists "docs/EXTREME_GAP_REPORT.md"
copy_if_exists "docs/FUNCTIONALITY_MATRIX_TESTNET_V1.md"
copy_if_exists "docs/MAINNET_PARITY.md"
copy_if_exists "docs/PRODUCT_RUNBOOK.md"
copy_if_exists "docs/PROTOCOL_INVARIANTS.md"
copy_if_exists "docs/DIFF_FROM_CANONICAL.md"
copy_if_exists "docs/RULES_ADDENDUM.md"

cp -R "$evidence_root" "$stage/evidence/"

(cd "$stage" && find . -type f -print0 | xargs -0 shasum -a 256 > SHA256SUMS.txt)

mkdir -p "$PROOF_DIR"
tar -czf "${PROOF_DIR}/${bundle_name}" -C "$stage" .
rm -rf "$stage"

echo "OK"
echo "PROOF_BUNDLE=${PROOF_DIR}/${bundle_name}"
echo "EVIDENCE_ROOT=${evidence_root}"
