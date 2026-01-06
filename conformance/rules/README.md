# Conformance Rules Index

Each rule file must include:
- Rule ID
- Status (enforced or placeholder)
- Severity
- Frozen reference
- Purpose
- Failure format
- Enforcement mechanism (if enforced)

Failure format
CONFORMANCE_FAIL|<RuleID>|<Severity>|<Summary>|<Path>:<Line>|<Match>

ID | Severity | Summary | Frozen reference | Enforcement
---|---|---|---|---
Q1-001 | critical | Wallet is not identity | frozen/q1/nyx_q_1_frozen_list.md Section 2.1 and 10 | grep patterns
Q1-002 | critical | No privileged fee exemptions | frozen/q1/nyx_q_1_frozen_list.md Section 2.3 and 10 | grep patterns
Q1-003 | high | Web2 is not a source of truth | frozen/q1/nyx_q_1_frozen_list.md Section 2.5 and 10 | placeholder
Q1-004 | critical | No trusted administrators | frozen/q1/nyx_q_1_frozen_list.md Section 2.2 | grep patterns