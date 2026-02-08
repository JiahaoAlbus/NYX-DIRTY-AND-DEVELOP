# NYX Release Verification

This document describes how to verify release artifacts, checksums, and evidence.

## 1) Build Artifacts

```bash
bash scripts/build_release_artifacts.sh
```

Artifacts are written to `release_artifacts/`.

## 2) Verify Checksums

```bash
cd release_artifacts
sha256sum -c SHA256SUMS.txt
```

## 3) Verify Manifest & SBOM

```bash
cat release_artifacts/manifest.json | jq .
cat release_artifacts/sbom.json | jq .
```

## 4) Verify Evidence & Replay

```bash
bash scripts/nyx_verify_all.sh --seed 123 --run-id extreme-testnet
bash scripts/nyx_pack_proof_artifacts.sh
```

Evidence appears under `docs/evidence/`, and proof bundles under `release_artifacts/proof/`.

## 5) Verify Web2 Guard

```bash
curl -sS http://127.0.0.1:8091/web2/v1/allowlist | jq .
```

## 6) Verify Portal

```bash
cd nyx-world
npm run build
```
