# Conformance System

Conformance is the enforcement layer for the NYX constitution and frozen rules.
It is the gate that rejects implementation changes that violate frozen constraints.

Entrypoint
- conformance/run.sh is the only supported entrypoint for CI and local runs.

Components
- conformance/frozen-verify.sh validates frozen/q1 integrity and duplicate sources.
- conformance/frozen-manifest.sha256 stores frozen file hashes outside the frozen directory.
- tooling/scripts/conformance.sh enforces rule patterns without scanning documentation.

Rules
- conformance/rules/ contains rule definitions with stable IDs.
- conformance/rules/patterns.txt binds enforceable patterns to rule IDs.

Failure output format
CONFORMANCE_FAIL|<RuleID>|<Severity>|<Summary>|<Path>:<Line>|<Match>