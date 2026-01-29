# NYX External Proof Package

## Purpose
This directory contains the canonical proof package for the NYX Project. It is designed to allow external auditors, grant evaluators, and technical partners to verify the project's claims, reproducibility, and architectural integrity without marketing fluff.

## Contents

- **[Technical Overview](./NYX_TECHNICAL_OVERVIEW.md)**: The canonical technical description of the NYX testnet portal infrastructure.
- **[Reproducibility Guide](./REPRODUCIBILITY.md)**: Instructions for running the one-command verification script and reproducing all artifacts.
- **[Demo Script](./DEMO_SCRIPT.md)**: A 10-minute guided tour of the system, including failure mode verification.
- **[Security Posture](./SECURITY_POSTURE.md)**: Details on determinism, invariants, gates, and the "no fake data" policy.
- **[What NYX Is Not](./WHAT_NYX_IS_NOT.md)**: Explicit non-goals and scope boundaries.
- **[Current Limitations](./CURRENT_LIMITATIONS.md)**: Known limitations of the current testnet implementation.

## Verification

To verify the entire project state (tests, conformance, smoke runs, builds), run:

```bash
bash scripts/nyx_verify_all.sh
```

To generate a redistributable proof package artifact:

```bash
bash scripts/nyx_pack_proof_artifacts.sh
```
