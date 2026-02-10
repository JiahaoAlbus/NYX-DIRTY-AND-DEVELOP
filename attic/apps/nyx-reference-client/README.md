# NYX Reference Client (v1)

Purpose
- Deterministic reference shell for Router v1 receipts and replay.

Scope
- CLI entry, deterministic report output, and replay verification.
- Deterministic step panel: reserves, LP, output, and fee_charged.

Non-Scope
- End-user UI or interactive flows.
- Key handling, secret storage, or any identity semantics.

Run
- `PYTHONPATH="apps/nyx-reference-client/src:packages/l3-router/src:packages/l3-dex/src" python -m nyx_reference_client.cli --seed 123 --out /tmp/nyx_ref_report.json`

Output
- Summary line with state_hash, receipt_chain, replay_ok.
- Step panel lines in stable order.
