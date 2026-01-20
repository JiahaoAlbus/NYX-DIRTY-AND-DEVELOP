# Extension Registry (Interface and Boundary Only)

## Purpose
Record placeholder extension domains and their boundary rules without implementing any feature logic.

## Scope
This registry lists future domains and their interface boundaries only.

## Non-Scope
- Any implementation commitment or delivery timeline.
- Any UI specification or integration detail.
- Any protocol semantics change.

## Normative Rules (MUST/MUST NOT)
- Registry entries MUST be interface placeholders only.
- Registry entries MUST NOT introduce protocol semantics or fee rule changes.
- Registry entries MUST NOT include secret material or non-deterministic inputs.
- Extensions MUST rely on protocol receipts and traces as authoritative evidence.
- Extensions MUST keep platform fees additive and follow Platform Fee Specification v1.

## Registry Entries (Placeholders)

| Domain | Placeholder Interface | Boundary Notes | Evidence | Status |
| --- | --- | --- | --- | --- |
| Shopping | ExtensionAdapter v1 | Uses receipts and traces only; no protocol changes. | Deterministic receipts and replay. | Placeholder |
| Chat | ExtensionAdapter v1 | Read-only consumption of evidence; no state mutation in protocol core. | Deterministic receipts and replay. | Placeholder |
| Entertainment | ExtensionAdapter v1 | Additive fee allowed at extension point only. | Deterministic receipts and replay. | Placeholder |

## Security and Abuse Boundaries
- Extensions MUST NOT claim protocol compliance without replayable evidence.
- Extensions MUST NOT introduce alternate state transitions outside protocol core.

## Evidence and Enforcement
- Conformance drills SHOULD validate that extensions do not alter protocol semantics.
- Determinism checks SHOULD confirm stable evidence outputs.

## Change Control
This registry is normative. Changes require a version bump and documented evidence of no protocol semantic drift.
