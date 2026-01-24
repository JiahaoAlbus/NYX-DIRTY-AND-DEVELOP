# Q10 Treasury and Fees (Testnet Beta)

## Purpose
Define the testnet treasury routing rules and fee invariants for Q10.

## Scope
- Testnet-only fee routing for value-moving actions.
- Treasury address resolution from local environment configuration.
- Auditability requirements for fee records.

## Non-Scope
- Mainnet treasury governance.
- External wallet integrations.
- Any fee waivers or privileged bypass paths.

## Definitions
- **Protocol fee**: The mandatory fee enforced by the sealed protocol fee engine.
- **Platform fee**: An additive overlay that MUST NOT replace or waive the protocol fee.
- **Treasury address**: The testnet vault destination configured locally.

## Normative Rules (MUST / MUST NOT)
1) Protocol fee MUST remain > 0 for any value-moving action.
2) Platform fee MUST be additive only and MUST NOT reduce or replace the protocol fee.
3) Fee routing MUST use `NYX_TESTNET_FEE_ADDRESS` provided via local env or `--env-file`.
4) If a fee address is missing, the system MUST fail fast for fee-bearing actions.
5) Fee ledger records MUST include module, action, protocol fee total, platform fee amount, total paid, fee address, and run_id.
6) Fee routing MUST be deterministic for identical inputs.
7) Fee routing MUST NOT depend on client identity or external accounts.

## Evidence / Verification
- Unit tests:
  - Fee totals remain > 0 for wallet transfers.
  - Platform fee is additive and never replaces protocol fee.
- Gateway storage:
  - Fee ledger entries are persisted and auditable.

## Freeze / Change Control
This document is normative for Q10 Testnet Beta. Changes require a versioned replacement document and regression evidence.
