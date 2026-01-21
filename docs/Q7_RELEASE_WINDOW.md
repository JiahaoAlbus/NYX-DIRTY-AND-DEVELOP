# Q7 Release Window

Purpose
- Define the final release window controls for Q7.

Scope
- Documentation and evidence only.

Non-Scope
- No protocol changes.
- No UI behavior changes.

Normative Rules
- Release window actions MUST be documented and reproducible.
- Any change during the window MUST be docs-only or patch-only with regression evidence.

Evidence and Verification
- Canonical tests:
  - python -m unittest discover -p "*_test.py" -v
- Evidence export:
  - scripts/q7_repro_one_shot.sh

Freeze and Change Control
- This window is final for Q7.
- Changes require regression evidence and explicit approval.
