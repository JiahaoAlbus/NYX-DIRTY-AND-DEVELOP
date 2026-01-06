# Conformance Roadmap

Phase 0: Pattern gate (current)
- Regex-based detection for frozen rule violations.
- Fast feedback with audit-friendly output.

Phase 1: Structured parsing
- Add AST-based analyzers per language.
- Enforce layer boundaries and interface contracts.

Phase 2: Dependency graph enforcement
- Build dependency graphs and reject illegal edges.
- Track transitive dependency drift and privilege escalation paths.

Phase 3: Policy-as-code
- Encode frozen rules as machine-readable policy.
- Enable deterministic, testable policy evaluation.

Phase 4: Formal verification targets
- Model critical invariants with proof obligations.
- Add formal checks where feasible.

Phase 5: Provenance and attestations
- SLSA-style build provenance and artifact signing.
- Evidence bundles for compliance audits.