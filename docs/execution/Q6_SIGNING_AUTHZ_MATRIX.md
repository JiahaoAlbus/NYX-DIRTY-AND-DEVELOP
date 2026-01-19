# Q6 Signing Authorization Matrix

Purpose
- Define required approvals for signing actions during Q6 operations.

Scope
- Operational signing roles and required approvals.

Non-Scope
- Any change to protocol or signing semantics.

MUST and MUST NOT
- Signing actions MUST have explicit approvals listed here.
- No single operator MUST be able to authorize all steps.
- The matrix MUST NOT include private keys or secrets.

Matrix
- Action: Build candidate release
  - Required approvals:
  - Evidence reference:
- Action: Publish tag (if allowed)
  - Required approvals:
  - Evidence reference:
- Action: Publish release notes
  - Required approvals:
  - Evidence reference:

Evidence / Verification
- Approval evidence stored as references in the Q6 evidence ledger.

Freeze / Change Control
- Execution-only policy; no protocol changes.
