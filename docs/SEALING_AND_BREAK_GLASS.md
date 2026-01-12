# Sealing & Break-Glass Rules

## Sealed Foundations (do not modify without break-glass)
- `packages/l0-identity/`
- `packages/l0-zk-id/`
- `packages/l2-economics/`
- `packages/l1-chain/`
- `packages/wallet-kernel/`
- `packages/e2e-demo/`
- `frozen/q1/`, `.github/workflows/`, `ci/`, `conformance/`, `tooling/scripts/`

## Break-Glass Requirements
Each break-glass change must document:
- Reason
- Risk
- Rollback
- Approver (Huangjiahao)

## Principles
- Week1–Week8 delivery is sealed; do not attempt to rework or refactor past milestones.
- Break-glass is a last resort for blocking defects; prefer additive packages and tests.
- No override flags or shortcuts are allowed to bypass gates.
