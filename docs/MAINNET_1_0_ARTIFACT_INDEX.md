# Mainnet 1.0 Artifact Index

How to reproduce
- `git fetch --tags`
- `git checkout -f mainnet-1.0`
- Open `docs/MAINNET_1_0_ARTIFACT_INDEX.md`

Anchor
- HEAD: `9e795f461931301344445286e463ce2450fc9a6c`
- Describe: `mainnet-1.0-attest`
- Tags at HEAD: `mainnet-1.0`, `mainnet-1.0-attest`

| Path | Classification | Purpose |
| --- | --- | --- |
| `attic/apps/nyx-first-app/src/nyx_first_app/__init__.py` | Implementation | Package export surface and public API wiring. |
| `attic/apps/nyx-first-app/src/nyx_first_app/app.py` | Implementation | Module logic for the package domain. |
| `attic/apps/nyx-first-app/src/nyx_first_app/cli.py` | Implementation | Deterministic CLI entrypoint for evidence runs. |
| `attic/apps/nyx-first-app/src/nyx_first_app/models.py` | Implementation | Module logic for the package domain. |
| `attic/apps/nyx-first-app/test/__init__.py` | Evidence | Package export surface and public API wiring. |
| `attic/apps/nyx-first-app/test/app_determinism_test.py` | Evidence | Module logic for the package domain. |
| `attic/apps/nyx-first-app/test/app_invalid_args_test.py` | Evidence | Module logic for the package domain. |
| `attic/apps/nyx-first-app/test/app_no_secret_leak_test.py` | Evidence | Module logic for the package domain. |
| `attic/apps/nyx-first-app/test/app_smoke_test.py` | Evidence | Module logic for the package domain. |
| `attic/apps/nyx-reference-client/src/nyx_reference_client/__init__.py` | Implementation | Package export surface and public API wiring. |
| `attic/apps/nyx-reference-client/src/nyx_reference_client/app.py` | Implementation | Module logic for the package domain. |
| `attic/apps/nyx-reference-client/src/nyx_reference_client/cli.py` | Implementation | Deterministic CLI entrypoint for evidence runs. |
| `attic/apps/nyx-reference-client/src/nyx_reference_client/models.py` | Implementation | Module logic for the package domain. |
| `attic/apps/nyx-reference-client/test/client_smoke_test.py` | Evidence | Module logic for the package domain. |
| `attic/apps/nyx-reference-client/test/determinism_guard_test.py` | Evidence | Module logic for the package domain. |
| `conformance/README.md` | Normative Spec | Conformance is the enforcement layer for the NYX constitution and frozen rules. |
| `conformance/ROADMAP.md` | Normative Spec | Phase 0: Pattern gate (current) |
| `conformance/frozen-manifest.sha256` | Operations | Conformance data or rule manifest. |
| `conformance/frozen-verify.sh` | Operations | Conformance gate script used by CI and local checks. |
| `conformance/rules/Q1-001.md` | Normative Spec | Status: enforced |
| `conformance/rules/Q1-002.md` | Normative Spec | Status: enforced |
| `conformance/rules/Q1-003.md` | Normative Spec | Status: placeholder |
| `conformance/rules/Q1-004.md` | Normative Spec | Status: enforced |
| `conformance/rules/README.md` | Normative Spec | Each rule file must include: |
| `conformance/rules/patterns.txt` | Operations | Conformance data or rule manifest. |
| `conformance/run.sh` | Operations | Conformance gate script used by CI and local checks. |
| `docs/AUDIT_CHECKLIST_TESTNET_0_1.md` | Operations | Phase 0 — Clean Room |
| `docs/AUDIT_CHECKLIST_TESTNET_0_2.md` | Operations | Phase 0 — Clean Room |
| `docs/AUDIT_PACK_Q5.md` | Operations | Purpose |
| `docs/AUDIT_REPRO_COMMANDS.md` | Operations | Title: Audit Repro Commands (Q5). |
| `docs/BUG_BOUNTY_PROGRAM.md` | Operations | Title: Bug Bounty Program. |
| `docs/BUG_BOUNTY_SEVERITY_RUBRIC.md` | Operations | Title: Bug Bounty Severity Rubric. |
| `docs/CHANGE_CONTROL.md` | Normative Spec | Title: Change Control. |
| `docs/DEX_SECURITY_CASE.md` | Normative Spec | Title: DEX Security Case. |
| `docs/DEX_V1_BLUEPRINT.md` | Normative Spec | Title: DEX v1 Blueprint. |
| `docs/DEX_V1_ROUTER_BLUEPRINT.md` | Normative Spec | Purpose |
| `docs/FORMAL_BOUND_NOTES.md` | Normative Spec | Title: Formal Bound Notes. |
| `docs/INVARIANTS_AND_GATES.md` | Normative Spec | Title: Invariants & Gates (Testnet 0.1). |
| `docs/INVARIANT_MAP_DEX.md` | Normative Spec | Title: DEX Invariant Map. |
| `docs/INVARIANT_MAP_DEX_V1.md` | Normative Spec | Purpose |
| `docs/MAINNET_LAUNCH_CHECKLIST.md` | Operations | Status: No-Go (Q5 RC pending) |
| `docs/NYX_Q3_IMMUTABLE_RULES.md` | Normative Spec | Title: NYX Q3 Immutable Rules. |
| `docs/PHASE2_PLAN.md` | Ecosystem-Platform | Boundary: protocol core remains sealed; Phase-2 is additive only. |
| `docs/POSITIONING_ONE_PAGER.md` | Ecosystem-Platform | Title: NYX Positioning (One Pager). |
| `docs/Q3_INTERFACES.md` | Ecosystem-Platform | This document describes the stub interfaces introduced for Q3 planning. |
| `docs/Q3_PRIVACY_TX_V1_SPEC.md` | Normative Spec | Title: Q3 Privacy Tx v1 Spec. |
| `docs/Q5_LANGUAGE_NORMALIZATION.md` | Deprecated-Legacy | Title: Q5 Language Normalization. |
| `docs/REFERENCE_CLIENT_SPEC.md` | Normative Spec | Purpose |
| `docs/RELEASE_NOTES_Q5_RC.md` | Operations | Purpose |
| `docs/RELEASE_NOTES_TESTNET_0_1.md` | Operations | Title: Release Notes — NYX Testnet 0.1. |
| `docs/RELEASE_NOTES_TESTNET_0_2.md` | Operations | Title: Testnet 0.2 — Release Notes. |
| `docs/RELEASE_PROCESS_Q5.md` | Operations | Title: Q5 Release Process. |
| `docs/SEALING_AND_BREAK_GLASS.md` | Normative Spec | Title: Sealing & Break-Glass Rules. |
| `docs/SECURITY_DISCLOSURE_PROCESS.md` | Operations | Title: Security Disclosure Process. |
| `docs/SECURITY_POSTURE.md` | Normative Spec | Title: Security Posture (Phase-2). |
| `docs/TESTNET_0_1_RUNBOOK.md` | Operations | Goal: a new user can validate the sealed stack and run the Week7 end-to-end demo in ~10 minutes. |
| `docs/WEEK10_13_HARDENING.md` | Normative Spec | Title: Week10–13 Buffer & Hardening. |
| `docs/audit/WEEK1_ENGINEERING_FOUNDATION_AUDIT.md` | Operations | Title: Week 1 Engineering Foundation Audit. |
| `docs/break-glass.md` | Normative Spec | This procedure applies to any change under frozen/q1. |
| `docs/engineering-foundation.md` | Normative Spec | This document describes the long-term engineering constraints for NYX. |
| `docs/execution/Q6_BOUNTY_LAUNCH_EVIDENCE.md` | Operations | Purpose |
| `docs/execution/Q6_CLOSEOUT_REPORT.md` | Operations | Purpose |
| `docs/execution/Q6_DISCLOSURE_INBOX_TEST.md` | Operations | Purpose |
| `docs/execution/Q6_DRYRUN_1_REPORT.md` | Operations | Purpose |
| `docs/execution/Q6_EVIDENCE_LEDGER_TEMPLATE.md` | Operations | Purpose |
| `docs/execution/Q6_EXECUTION_PLAN.md` | Operations | Purpose |
| `docs/execution/Q6_FINAL_STATE.md` | Operations | Purpose |
| `docs/execution/Q6_INCIDENT_DRILL_REPORT.md` | Operations | Purpose |
| `docs/execution/Q6_KEY_CEREMONY_V1_EVIDENCE.md` | Operations | Purpose |
| `docs/execution/Q6_LIVE_RELEASE_REPORT.md` | Operations | Purpose |
| `docs/execution/Q6_OPS_HARDENING_REPORT.md` | Operations | Purpose |
| `docs/execution/Q6_PATCHLOG_1.md` | Operations | Purpose |
| `docs/execution/Q6_PROVENANCE_PACK.md` | Operations | Purpose |
| `docs/execution/Q6_PUBLIC_USAGE_CONTRACT.md` | Operations | Purpose |
| `docs/execution/Q6_RELEASE_NOTES_RC.md` | Operations | Purpose |
| `docs/execution/Q6_RELEASE_WINDOW_PLAN.md` | Operations | Purpose |
| `docs/execution/Q6_SECURITY_GATE_REPORT.md` | Operations | Purpose |
| `docs/execution/Q6_SIGNING_AUTHZ_MATRIX.md` | Operations | Purpose |
| `docs/ops/week2_acceptance_report.md` | Operations | Summary |
| `docs/week1-plan.md` | Normative Spec | Title: week1-plan.md. |
| `packages/conformance-v1/src/conformance_v1/__init__.py` | Evidence | Package export surface and public API wiring. |
| `packages/conformance-v1/src/conformance_v1/drills.py` | Evidence | Module logic for the package domain. |
| `packages/conformance-v1/src/conformance_v1/model.py` | Evidence | Module logic for the package domain. |
| `packages/conformance-v1/src/conformance_v1/report.py` | Evidence | Module logic for the package domain. |
| `packages/conformance-v1/src/conformance_v1/ruleset.py` | Evidence | Module logic for the package domain. |
| `packages/conformance-v1/src/conformance_v1/runner.py` | Evidence | Module logic for the package domain. |
| `packages/conformance-v1/src/conformance_v1/scans.py` | Evidence | Module logic for the package domain. |
| `packages/conformance-v1/test/guard_no_false_negative_test.py` | Evidence | Module logic for the package domain. |
| `packages/conformance-v1/test/guard_no_false_positive_regression_test.py` | Evidence | Module logic for the package domain. |
| `packages/conformance-v1/test/guard_no_frozen_gate_sequence_test.py` | Evidence | Module logic for the package domain. |
| `packages/conformance-v1/test/guard_ruleset_non_dilution_test.py` | Evidence | Module logic for the package domain. |
| `packages/conformance-v1/test/report_schema_test.py` | Evidence | Module logic for the package domain. |
| `packages/conformance-v1/test/runner_outfile_test.py` | Evidence | Module logic for the package domain. |
| `packages/conformance-v1/test/runtime_drills_illegal_shortcuts_test.py` | Evidence | Module logic for the package domain. |
| `packages/conformance-v1/test/tamper_drills_stricter_test.py` | Evidence | Module logic for the package domain. |
| `packages/conformance-v1/test/unit_report_test.py` | Evidence | Module logic for the package domain. |
| `packages/conformance-v1/test/unit_ruleset_test.py` | Evidence | Module logic for the package domain. |
| `packages/conformance-v1/test/unit_scans_test.py` | Evidence | Module logic for the package domain. |
| `packages/e2e-demo/src/e2e_demo/__init__.py` | Evidence | Package export surface and public API wiring. |
| `packages/e2e-demo/src/e2e_demo/canonical.py` | Evidence | Canonical encoding helpers with type checks. |
| `packages/e2e-demo/src/e2e_demo/hashing.py` | Evidence | SHA-256 helpers and framing utilities. |
| `packages/e2e-demo/src/e2e_demo/pipeline.py` | Evidence | Module logic for the package domain. |
| `packages/e2e-demo/src/e2e_demo/replay.py` | Evidence | Deterministic replay logic from receipts or traces. |
| `packages/e2e-demo/src/e2e_demo/run_demo.py` | Evidence | Deterministic CLI entrypoint for evidence runs. |
| `packages/e2e-demo/src/e2e_demo/trace.py` | Evidence | Trace schema and serialization helpers. |
| `packages/e2e-demo/test/e2e_smoke_test.py` | Evidence | Module logic for the package domain. |
| `packages/e2e-demo/test/guard_trace_leak_test.py` | Evidence | Module logic for the package domain. |
| `packages/e2e-private-transfer/src/e2e_private_transfer/__init__.py` | Evidence | Package export surface and public API wiring. |
| `packages/e2e-private-transfer/src/e2e_private_transfer/canonical.py` | Evidence | Canonical encoding helpers with type checks. |
| `packages/e2e-private-transfer/src/e2e_private_transfer/hashing.py` | Evidence | SHA-256 helpers and framing utilities. |
| `packages/e2e-private-transfer/src/e2e_private_transfer/pipeline.py` | Evidence | Module logic for the package domain. |
| `packages/e2e-private-transfer/src/e2e_private_transfer/replay.py` | Evidence | Deterministic replay logic from receipts or traces. |
| `packages/e2e-private-transfer/src/e2e_private_transfer/run_demo.py` | Evidence | Deterministic CLI entrypoint for evidence runs. |
| `packages/e2e-private-transfer/src/e2e_private_transfer/trace.py` | Evidence | Trace schema and serialization helpers. |
| `packages/e2e-private-transfer/test/determinism_test.py` | Evidence | Module logic for the package domain. |
| `packages/e2e-private-transfer/test/e2e_smoke_test.py` | Evidence | Module logic for the package domain. |
| `packages/e2e-private-transfer/test/guard_no_secret_leak_test.py` | Evidence | Module logic for the package domain. |
| `packages/e2e-private-transfer/test/tamper_matrix_test.py` | Evidence | Module logic for the package domain. |
| `packages/l0-identity/src/__init__.py` | Implementation | Package export surface and public API wiring. |
| `packages/l0-identity/src/identity.py` | Implementation | Module logic for the package domain. |
| `packages/l0-identity/test/__init__.py` | Evidence | Package export surface and public API wiring. |
| `packages/l0-identity/test/conformance_v1_bridge_test.py` | Evidence | Module logic for the package domain. |
| `packages/l0-identity/test/identity_test.py` | Evidence | Module logic for the package domain. |
| `packages/l0-identity/test/l1_chain_bridge_test.py` | Evidence | Module logic for the package domain. |
| `packages/l0-identity/test/l2_economics_bridge_test.py` | Evidence | Module logic for the package domain. |
| `packages/l0-identity/test/q3_bridge_test.py` | Evidence | Module logic for the package domain. |
| `packages/l0-identity/test/wallet_kernel_bridge_test.py` | Evidence | Module logic for the package domain. |
| `packages/l0-identity/test/week10_13_bridge_test.py` | Evidence | Module logic for the package domain. |
| `packages/l0-identity/test/week7_e2e_bridge_test.py` | Evidence | Module logic for the package domain. |
| `packages/l0-identity/test/zkid_extreme_bridge_test.py` | Evidence | Module logic for the package domain. |
| `packages/l0-reputation/src/l0_reputation/__init__.py` | Implementation | Package export surface and public API wiring. |
| `packages/l0-reputation/src/l0_reputation/errors.py` | Implementation | Domain error types for deterministic failure paths. |
| `packages/l0-reputation/src/l0_reputation/events.py` | Implementation | Module logic for the package domain. |
| `packages/l0-reputation/src/l0_reputation/fee_binding.py` | Implementation | Fee engine adaptation and enforcement hooks. |
| `packages/l0-reputation/src/l0_reputation/hashing.py` | Implementation | SHA-256 helpers and framing utilities. |
| `packages/l0-reputation/src/l0_reputation/interfaces.py` | Implementation | Interface or protocol definitions without implementation. |
| `packages/l0-reputation/src/l0_reputation/kernel.py` | Implementation | State transition functions and core apply logic. |
| `packages/l0-reputation/src/l0_reputation/state.py` | Implementation | State data structures and state hash helpers. |
| `packages/l0-reputation/src/l0_reputation/types.py` | Implementation | Type helpers and validators for domain values. |
| `packages/l0-reputation/test/__init__.py` | Evidence | Package export surface and public API wiring. |
| `packages/l0-reputation/test/guard_context_binding_test.py` | Evidence | Module logic for the package domain. |
| `packages/l0-reputation/test/property_reputation_invariants_test.py` | Evidence | Module logic for the package domain. |
| `packages/l0-reputation/test/skeleton_import_test.py` | Evidence | Module logic for the package domain. |
| `packages/l0-reputation/test/unit_context_binding_test.py` | Evidence | Module logic for the package domain. |
| `packages/l0-reputation/test/unit_fee_nonzero_test.py` | Evidence | Module logic for the package domain. |
| `packages/l0-reputation/test/unit_root_recompute_test.py` | Evidence | Module logic for the package domain. |
| `packages/l0-reputation/test/unit_sponsor_equivalence_test.py` | Evidence | Module logic for the package domain. |
| `packages/l0-zk-id/src/__init__.py` | Implementation | Package export surface and public API wiring. |
| `packages/l0-zk-id/src/binding.py` | Implementation | Module logic for the package domain. |
| `packages/l0-zk-id/src/canonical.py` | Implementation | Canonical encoding helpers with type checks. |
| `packages/l0-zk-id/src/envelope.py` | Implementation | Module logic for the package domain. |
| `packages/l0-zk-id/src/nullifier.py` | Implementation | Module logic for the package domain. |
| `packages/l0-zk-id/src/prover/__init__.py` | Implementation | Package export surface and public API wiring. |
| `packages/l0-zk-id/src/prover/mock.py` | Implementation | Module logic for the package domain. |
| `packages/l0-zk-id/src/verifier.py` | Implementation | Module logic for the package domain. |
| `packages/l0-zk-id/test/__init__.py` | Evidence | Package export surface and public API wiring. |
| `packages/l0-zk-id/test/envelope_validation_test.py` | Evidence | Module logic for the package domain. |
| `packages/l0-zk-id/test/guard_mutation_prevention_test.py` | Evidence | Module logic for the package domain. |
| `packages/l0-zk-id/test/property_context_separation_test.py` | Evidence | Module logic for the package domain. |
| `packages/l0-zk-id/test/unit_context_separation_test.py` | Evidence | Module logic for the package domain. |
| `packages/l1-chain/src/l1_chain/__init__.py` | Implementation | Package export surface and public API wiring. |
| `packages/l1-chain/src/l1_chain/adapter.py` | Implementation | Module logic for the package domain. |
| `packages/l1-chain/src/l1_chain/canonical.py` | Implementation | Canonical encoding helpers with type checks. |
| `packages/l1-chain/src/l1_chain/devnet/__init__.py` | Implementation | Package export surface and public API wiring. |
| `packages/l1-chain/src/l1_chain/devnet/adapter.py` | Implementation | Module logic for the package domain. |
| `packages/l1-chain/src/l1_chain/devnet/run_devnet.py` | Implementation | Module logic for the package domain. |
| `packages/l1-chain/src/l1_chain/hashing.py` | Implementation | SHA-256 helpers and framing utilities. |
| `packages/l1-chain/src/l1_chain/types.py` | Implementation | Type helpers and validators for domain values. |
| `packages/l1-chain/test/guard_no_identity_regression_test.py` | Evidence | Module logic for the package domain. |
| `packages/l1-chain/test/property_chain_invariants_test.py` | Evidence | Module logic for the package domain. |
| `packages/l1-chain/test/unit_chain_adapter_test.py` | Evidence | Module logic for the package domain. |
| `packages/l2-economics/src/__init__.py` | Implementation | Package export surface and public API wiring. |
| `packages/l2-economics/src/action.py` | Implementation | Module logic for the package domain. |
| `packages/l2-economics/src/canonical.py` | Implementation | Canonical encoding helpers with type checks. |
| `packages/l2-economics/src/engine.py` | Implementation | Module logic for the package domain. |
| `packages/l2-economics/src/fee.py` | Implementation | Module logic for the package domain. |
| `packages/l2-economics/src/hashing.py` | Implementation | SHA-256 helpers and framing utilities. |
| `packages/l2-economics/src/quote.py` | Implementation | Module logic for the package domain. |
| `packages/l2-economics/test/guard_no_bypass_regression_test.py` | Evidence | Module logic for the package domain. |
| `packages/l2-economics/test/property_fee_invariants_test.py` | Evidence | Module logic for the package domain. |
| `packages/l2-economics/test/unit_fee_engine_test.py` | Evidence | Module logic for the package domain. |
| `packages/l2-private-ledger/src/l2_private_ledger/__init__.py` | Implementation | Package export surface and public API wiring. |
| `packages/l2-private-ledger/src/l2_private_ledger/actions.py` | Implementation | Action types and payload schemas for state transitions. |
| `packages/l2-private-ledger/src/l2_private_ledger/errors.py` | Implementation | Domain error types for deterministic failure paths. |
| `packages/l2-private-ledger/src/l2_private_ledger/fee_binding.py` | Implementation | Fee engine adaptation and enforcement hooks. |
| `packages/l2-private-ledger/src/l2_private_ledger/interfaces.py` | Implementation | Interface or protocol definitions without implementation. |
| `packages/l2-private-ledger/src/l2_private_ledger/kernel.py` | Implementation | State transition functions and core apply logic. |
| `packages/l2-private-ledger/src/l2_private_ledger/proof_wiring.py` | Implementation | Module logic for the package domain. |
| `packages/l2-private-ledger/src/l2_private_ledger/state.py` | Implementation | State data structures and state hash helpers. |
| `packages/l2-private-ledger/src/l2_private_ledger/trace.py` | Implementation | Trace schema and serialization helpers. |
| `packages/l2-private-ledger/src/l2_private_ledger/types.py` | Implementation | Type helpers and validators for domain values. |
| `packages/l2-private-ledger/test/__init__.py` | Evidence | Package export surface and public API wiring. |
| `packages/l2-private-ledger/test/guard_binding_fields_mandatory_test.py` | Evidence | Module logic for the package domain. |
| `packages/l2-private-ledger/test/guard_compare_digest_usage_test.py` | Evidence | Module logic for the package domain. |
| `packages/l2-private-ledger/test/guard_fee_independent_of_payer_test.py` | Evidence | Module logic for the package domain. |
| `packages/l2-private-ledger/test/guard_framing_anti_ambiguity_test.py` | Evidence | Module logic for the package domain. |
| `packages/l2-private-ledger/test/guard_no_sender_semantics_test.py` | Evidence | Module logic for the package domain. |
| `packages/l2-private-ledger/test/property_context_statement_separation_test.py` | Evidence | Module logic for the package domain. |
| `packages/l2-private-ledger/test/property_fee_binding_test.py` | Evidence | Module logic for the package domain. |
| `packages/l2-private-ledger/test/property_private_ledger_test.py` | Evidence | Module logic for the package domain. |
| `packages/l2-private-ledger/test/skeleton_import_test.py` | Evidence | Module logic for the package domain. |
| `packages/l2-private-ledger/test/unit_bytes32_test.py` | Evidence | Module logic for the package domain. |
| `packages/l2-private-ledger/test/unit_double_spend_test.py` | Evidence | Module logic for the package domain. |
| `packages/l2-private-ledger/test/unit_enforce_paid_vector_exact_test.py` | Evidence | Module logic for the package domain. |
| `packages/l2-private-ledger/test/unit_fee_nonzero_test.py` | Evidence | Module logic for the package domain. |
| `packages/l2-private-ledger/test/unit_kernel_test.py` | Evidence | Module logic for the package domain. |
| `packages/l2-private-ledger/test/unit_proof_wiring_happy_path_test.py` | Evidence | Module logic for the package domain. |
| `packages/l2-private-ledger/test/unit_sponsor_equivalence_test.py` | Evidence | Module logic for the package domain. |
| `packages/l2-private-ledger/test/unit_state_root_test.py` | Evidence | Module logic for the package domain. |
| `packages/l2-private-ledger/test/unit_statement_validation_test.py` | Evidence | Module logic for the package domain. |
| `packages/l2-private-ledger/test/unit_tamper_fields_test.py` | Evidence | Module logic for the package domain. |
| `packages/l2-private-ledger/test/unit_tamper_replay_test.py` | Evidence | Module logic for the package domain. |
| `packages/l3-dex/src/l3_dex/__init__.py` | Implementation | Package export surface and public API wiring. |
| `packages/l3-dex/src/l3_dex/actions.py` | Implementation | Action types and payload schemas for state transitions. |
| `packages/l3-dex/src/l3_dex/errors.py` | Implementation | Domain error types for deterministic failure paths. |
| `packages/l3-dex/src/l3_dex/invariants.py` | Implementation | Invariant checks for bounded or runtime validation. |
| `packages/l3-dex/src/l3_dex/kernel.py` | Implementation | State transition functions and core apply logic. |
| `packages/l3-dex/src/l3_dex/receipts.py` | Implementation | Receipt schema and stable serialization fields. |
| `packages/l3-dex/src/l3_dex/replay.py` | Implementation | Deterministic replay logic from receipts or traces. |
| `packages/l3-dex/src/l3_dex/state.py` | Implementation | State data structures and state hash helpers. |
| `packages/l3-dex/test/bounded_explorer_test.py` | Evidence | Module logic for the package domain. |
| `packages/l3-dex/test/skeleton_import_test.py` | Evidence | Module logic for the package domain. |
| `packages/l3-router/src/l3_router/__init__.py` | Implementation | Package export surface and public API wiring. |
| `packages/l3-router/src/l3_router/actions.py` | Implementation | Action types and payload schemas for state transitions. |
| `packages/l3-router/src/l3_router/errors.py` | Implementation | Domain error types for deterministic failure paths. |
| `packages/l3-router/src/l3_router/fee_binding.py` | Implementation | Fee engine adaptation and enforcement hooks. |
| `packages/l3-router/src/l3_router/invariants.py` | Implementation | Invariant checks for bounded or runtime validation. |
| `packages/l3-router/src/l3_router/kernel.py` | Implementation | State transition functions and core apply logic. |
| `packages/l3-router/src/l3_router/receipts.py` | Implementation | Receipt schema and stable serialization fields. |
| `packages/l3-router/src/l3_router/replay.py` | Implementation | Deterministic replay logic from receipts or traces. |
| `packages/l3-router/src/l3_router/state.py` | Implementation | State data structures and state hash helpers. |
| `packages/l3-router/test/golden_vectors_test.py` | Evidence | Module logic for the package domain. |
| `packages/l3-router/test/property_router_invariants_test.py` | Evidence | Module logic for the package domain. |
| `packages/l3-router/test/skeleton_import_test.py` | Evidence | Module logic for the package domain. |
| `packages/l3-router/test/unit_atomic_failure_test.py` | Evidence | Module logic for the package domain. |
| `packages/l3-router/test/unit_bounds_test.py` | Evidence | Module logic for the package domain. |
| `packages/l3-router/test/unit_enforce_paid_vector_exact_test.py` | Evidence | Module logic for the package domain. |
| `packages/l3-router/test/unit_fee_nonzero_test.py` | Evidence | Module logic for the package domain. |
| `packages/l3-router/test/unit_rejects_invalid_swap_test.py` | Evidence | Module logic for the package domain. |
| `packages/l3-router/test/unit_replay_test.py` | Evidence | Module logic for the package domain. |
| `packages/l3-router/test/unit_sponsor_equivalence_test.py` | Evidence | Module logic for the package domain. |
| `packages/q3-interfaces/src/q3_interfaces/__init__.py` | Ecosystem-Platform | Package export surface and public API wiring. |
| `packages/q3-interfaces/src/q3_interfaces/interfaces.py` | Ecosystem-Platform | Interface or protocol definitions without implementation. |
| `packages/q3-interfaces/src/q3_interfaces/types.py` | Ecosystem-Platform | Type helpers and validators for domain values. |
| `packages/q3-interfaces/test/__init__.py` | Evidence | Package export surface and public API wiring. |
| `packages/q3-interfaces/test/q3_interfaces_import_test.py` | Evidence | Module logic for the package domain. |
| `packages/q3-interfaces/test/q3_interfaces_no_runtime_dependency_test.py` | Evidence | Module logic for the package domain. |
| `packages/wallet-kernel/src/wallet_kernel/__init__.py` | Implementation | Package export surface and public API wiring. |
| `packages/wallet-kernel/src/wallet_kernel/canonical.py` | Implementation | Canonical encoding helpers with type checks. |
| `packages/wallet-kernel/src/wallet_kernel/errors.py` | Implementation | Domain error types for deterministic failure paths. |
| `packages/wallet-kernel/src/wallet_kernel/kernel.py` | Implementation | State transition functions and core apply logic. |
| `packages/wallet-kernel/src/wallet_kernel/keystore.py` | Implementation | Module logic for the package domain. |
| `packages/wallet-kernel/src/wallet_kernel/limits.py` | Implementation | Module logic for the package domain. |
| `packages/wallet-kernel/src/wallet_kernel/multisig.py` | Implementation | Module logic for the package domain. |
| `packages/wallet-kernel/src/wallet_kernel/policy.py` | Implementation | Module logic for the package domain. |
| `packages/wallet-kernel/src/wallet_kernel/proof_plumbing.py` | Implementation | Module logic for the package domain. |
| `packages/wallet-kernel/src/wallet_kernel/recovery.py` | Implementation | Module logic for the package domain. |
| `packages/wallet-kernel/src/wallet_kernel/secrets.py` | Implementation | Module logic for the package domain. |
| `packages/wallet-kernel/src/wallet_kernel/signing.py` | Implementation | Module logic for the package domain. |
| `packages/wallet-kernel/src/wallet_kernel/tx_plumbing.py` | Implementation | Module logic for the package domain. |
| `packages/wallet-kernel/test/guard_no_privilege_escalation_test.py` | Evidence | Module logic for the package domain. |
| `packages/wallet-kernel/test/property_wallet_kernel_invariants_test.py` | Evidence | Module logic for the package domain. |
| `packages/wallet-kernel/test/unit_wallet_kernel_test.py` | Evidence | Module logic for the package domain. |
