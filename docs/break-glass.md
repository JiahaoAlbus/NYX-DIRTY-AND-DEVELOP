# Break-Glass Procedure

This procedure applies to any change under frozen/q1.
It is a last-resort process and must be auditable.

## Preconditions
- A written rationale describing why the change is unavoidable.
- Approval from the protocol lead and security owner.
- A linked tracking issue describing scope, impact, and rollback.

## Required change set
- Update frozen/q1 artifacts.
- Regenerate conformance/frozen-manifest.sha256.
- Update conformance mapping if the frozen list changes.
- Add a clear audit note in the PR description.
- PR description must include: Reason, Risk, Rollback, Approver.

## Review and verification
- PR must include red-team steps demonstrating CI protection behavior.
- All approvals must be recorded in the PR timeline.
- CI logs must show manifest verification and frozen lock signals.

## Post-merge audit
- Record the change in the release log.
- Reconfirm downstream conformance rules and documentation.
