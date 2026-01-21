# Q7 Release Notes (RC)

Purpose
- Record the release candidate scope and evidence for Q7.

Scope
- Reference UI, evidence export, platform fee hook, and conformance drills.

Non-Scope
- No protocol semantic changes.
- No live network claims.

Shipped
- Reference UI and backend wrapper for deterministic evidence export.
- Platform fee hook (additive only).
- Conformance drills for output contract and UI copy guard.

Not Shipped
- Any protocol changes or on-chain integration beyond sealed baseline.

Evidence and Verification
- python -m unittest discover -p "*_test.py" -v
- scripts/q7_repro_one_shot.sh

Freeze and Change Control
- This RC is a freeze checkpoint for Q7.
- Changes after RC must be docs or patch-only with regression evidence.
