# Q10 World Product Requirements

## Purpose
Define the Q10 Testnet Beta product requirements for the NYX world entrance without changing sealed protocol semantics.

## Scope
Applies to the NYX iOS super‑app shell and backend gateway for Testnet Beta.

## Non-Scope
No protocol semantic changes, no mainnet claims, no external wallet integration.

## Normative Requirements (MUST / MUST NOT)
- The product MUST provide a single entry to Wallet, Exchange, Marketplace, Chat, Entertainment, Settings, and Trust Center.
- The product MUST label all content as Testnet Beta.
- The product MUST NOT include login or signup flows.
- The product MUST NOT claim live operational status or real market data.
- The product MUST require explicit seed input for deterministic runs.
- Evidence fields MUST be displayed and exported verbatim.
- The product MUST NOT compute or alter evidence fields.

## Evidence / Verification
- python -m compileall packages/l0-identity/src
- python scripts/nyx_run_all_unittests.py
- PYTHONPATH="packages/conformance-v1/src" python -m conformance_v1.runner --out nyx_conformance_report.json

## Freeze / Change Control
- Q1–Q9 semantics remain sealed.
- Q10 changes are additive and must not alter deterministic outputs for existing evidence flows.
