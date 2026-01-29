# Security Posture

## Purpose
To outline the security principles, invariants, and mechanisms enforced in the NYX project.

## Core Principles

1.  **Determinism as Security**: Security relies on the property that `Output = Function(Input, State)`. Any deviation is evidence of tampering or a bug.
2.  **Evidence-First**: No operation is considered "complete" until an Evidence Bundle is generated and hashed.
3.  **Fail-Secure**: If an invariant is violated, the system halts or rejects the transaction rather than proceeding in an invalid state.

## Invariants & Gates

The `conformance-v1` package enforces the following:

-   **Fee Invariant**: `fee >= min_fee`. Transactions with insufficient fees are rejected.
-   **Platform Fee Additivity**: `total_fee = protocol_fee + platform_fee`. Platforms cannot subsidize protocol fees from the user's perspective (anti-spoofing).
-   **No Fake Data**: Code paths are scanned to ensure no `return True`, `return "ok"`, or mock objects are used in critical logic paths (verified by `no_fake_code_check.py`).

## Threat Model Assumptions

-   **Trusted Backend (for Testnet)**: We assume the backend is honest-but-lazy. It must produce valid evidence, or the client can prove malfeasance (by replaying the input).
-   **Client Integrity**: Clients verify the `state_hash` sequence. If a hash mismatch occurs, the client alerts the user.
-   **Transport Security**: Standard TLS is assumed for the gateway API (though local tests run over HTTP).

## Audit History

-   **Internal Audits**: Weekly code reviews and "Red Team" drills (e.g., trying to bypass fee checks).
-   **Automated Scans**: `nyx_verify_all.sh` runs static analysis and conformance checks on every build.
