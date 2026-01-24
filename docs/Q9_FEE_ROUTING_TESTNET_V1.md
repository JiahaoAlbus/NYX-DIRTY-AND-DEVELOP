# Q9 Testnet Fee Routing v1

## Purpose
Define Testnet Alpha fee routing rules for Q9 exchange actions with deterministic evidence.

## Scope
- Protocol fee enforcement for exchange actions.
- Additive platform fee overlay when configured.
- Routing to a configurable Testnet fee address.

## Non-Scope
- No fee waivers or discounts.
- No changes to sealed protocol fee semantics.

## Definitions
- **Protocol fee**: The mandatory fee from the core fee engine for shared-state mutation.
- **Platform fee**: An additive overlay fee applied at explicit extension points.
- **Fee address**: Testnet sink address provided via environment configuration.

## Normative Rules (MUST / MUST NOT)
- Protocol fee MUST remain mandatory and greater than zero for exchange mutations.
- Platform fee MUST be additive only and MUST NOT replace the protocol fee.
- The total paid amount MUST equal protocol fee total plus platform fee amount.
- The fee address MUST be provided via environment configuration.
- Missing or invalid fee address MUST cause deterministic failure.
- Fee routing MUST be recorded in a deterministic fee ledger entry.
- Fee routing MUST NOT alter evidence fields or ordering.

## Evidence and Auditability
- Fee ledger entries MUST be persisted with deterministic identifiers.
- Evidence exports MUST remain deterministic and replayable.

## Freeze / Change Control
- This fee routing spec is normative for Q9 Testnet Alpha.
- Changes require an explicit version bump and regression evidence.
