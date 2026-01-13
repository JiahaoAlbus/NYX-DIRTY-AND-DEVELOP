from __future__ import annotations

from conformance_v1.model import Rule

ADVERSARY_CLASSES = (
    "Nation-State Actors",
    "Platform-Level Adversaries",
    "Onchain Analytics Firms",
    "External Hackers",
    "Internal Malicious Actors",
)

DETECTION_STATIC = "static scan"
DETECTION_RUNTIME = "runtime drill"
DETECTION_BOTH = "both"
REPRO_COMMAND = (
    'PYTHONPATH="packages/conformance-v1/src" '
    "python -m conformance_v1.runner --out /tmp/nyx_conformance_report.json"
)

RULES: tuple[Rule, ...] = (
    Rule(
        rule_id="Q1-ID-01",
        adversary_class=("Internal Malicious Actors", "External Hackers"),
        attack_vector="address-as-id flags",
        surface="ID/Codebase",
        severity="BLOCKER",
        rationale="Account/address must not become id in code paths.",
        detection=DETECTION_STATIC,
        repro_command=REPRO_COMMAND,
    ),
    Rule(
        rule_id="Q1-ID-02",
        adversary_class=("Internal Malicious Actors", "External Hackers"),
        attack_vector="sender used as id",
        surface="ID/Codebase",
        severity="HIGH",
        rationale="Runtime should reject account-like identifiers as id.",
        detection=DETECTION_RUNTIME,
        repro_command=REPRO_COMMAND,
    ),
    Rule(
        rule_id="Q1-FEE-01",
        adversary_class=("External Hackers",),
        attack_vector="mutation fee evasion",
        surface="Economic Layer",
        severity="BLOCKER",
        rationale="State mutation must never be free.",
        detection=DETECTION_RUNTIME,
        repro_command=REPRO_COMMAND,
    ),
    Rule(
        rule_id="Q1-FEE-02",
        adversary_class=("External Hackers",),
        attack_vector="sponsor amount mutation",
        surface="Economic Layer",
        severity="HIGH",
        rationale="Sponsorship cannot change the fee amount.",
        detection=DETECTION_RUNTIME,
        repro_command=REPRO_COMMAND,
    ),
    Rule(
        rule_id="Q1-ZK-01",
        adversary_class=("Onchain Analytics Firms", "External Hackers"),
        attack_vector="cross-context proof reuse",
        surface="ID/Ledger",
        severity="BLOCKER",
        rationale="Proofs must be context-separated.",
        detection=DETECTION_RUNTIME,
        repro_command=REPRO_COMMAND,
    ),
    Rule(
        rule_id="Q1-ZK-02",
        adversary_class=("Onchain Analytics Firms", "External Hackers"),
        attack_vector="nullifier reuse across context",
        surface="ID/Ledger",
        severity="HIGH",
        rationale="Nullifier must bind to context to prevent reuse.",
        detection=DETECTION_RUNTIME,
        repro_command=REPRO_COMMAND,
    ),
    Rule(
        rule_id="Q1-SECRET-01",
        adversary_class=("Platform-Level Adversaries", "External Hackers"),
        attack_vector="root secret exfiltration",
        surface="Client/SDK",
        severity="BLOCKER",
        rationale="Root secret must not leak to outputs or trace.",
        detection=DETECTION_RUNTIME,
        repro_command=REPRO_COMMAND,
    ),
    Rule(
        rule_id="Q1-TRACE-01",
        adversary_class=("External Hackers",),
        attack_vector="trace tamper replay",
        surface="Protocol Logic",
        severity="HIGH",
        rationale="Tampered trace must fail replay verification.",
        detection=DETECTION_RUNTIME,
        repro_command=REPRO_COMMAND,
    ),
    Rule(
        rule_id="Q1-TRACE-02",
        adversary_class=("External Hackers",),
        attack_vector="fee tamper replay",
        surface="Economic Layer",
        severity="HIGH",
        rationale="Fee tampering must fail replay verification.",
        detection=DETECTION_RUNTIME,
        repro_command=REPRO_COMMAND,
    ),
    Rule(
        rule_id="Q1-TRACE-03",
        adversary_class=("External Hackers",),
        attack_vector="proof tamper replay",
        surface="ID/Ledger",
        severity="HIGH",
        rationale="Proof tampering must fail replay verification.",
        detection=DETECTION_RUNTIME,
        repro_command=REPRO_COMMAND,
    ),
    Rule(
        rule_id="Q1-PRIV-01",
        adversary_class=("Internal Malicious Actors",),
        attack_vector="unauthorized shortcut routes",
        surface="Upgrade Path/Codebase",
        severity="BLOCKER",
        rationale="No backdoor or unauthorized shortcut routes permitted.",
        detection=DETECTION_STATIC,
        repro_command=REPRO_COMMAND,
    ),
    Rule(
        rule_id="Q1-PLAT-01",
        adversary_class=("Nation-State Actors", "Platform-Level Adversaries"),
        attack_vector="forced compliance gateway",
        surface="Distribution/Access",
        severity="MEDIUM",
        rationale="Backdoor gating (KYC/allow) is not permitted.",
        detection=DETECTION_STATIC,
        repro_command=REPRO_COMMAND,
    ),
    Rule(
        rule_id="Q1-ANALYTICS-01",
        adversary_class=("Onchain Analytics Firms",),
        attack_vector="full commitment correlation",
        surface="Ledger/ID",
        severity="MEDIUM",
        rationale="Do not persist full commitment identifiers in shared state.",
        detection=DETECTION_STATIC,
        repro_command=REPRO_COMMAND,
    ),
)
