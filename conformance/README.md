# Conformance System

Conformance is the enforcement layer for the NYX constitution and frozen rules.
It is the gate that rejects implementation changes that violate frozen constraints.

Entrypoint
- conformance/run.sh (CI calls this entrypoint)
- tooling/scripts/conformance.sh (current enforcement engine)

Rules
- conformance/rules/ contains rule definitions with stable IDs (for example Q1-001).
- Rule IDs map to frozen list items for traceability.