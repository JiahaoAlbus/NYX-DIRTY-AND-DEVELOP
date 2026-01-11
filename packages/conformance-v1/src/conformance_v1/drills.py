from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

from conformance_v1.model import DrillResult


def _ensure_paths() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    paths = [
        repo_root / "packages" / "l0-identity" / "src",
        repo_root / "packages" / "l0-zk-id" / "src",
        repo_root / "packages" / "l2-economics" / "src",
        repo_root / "packages" / "l1-chain" / "src",
        repo_root / "packages" / "wallet-kernel" / "src",
        repo_root / "packages" / "e2e-demo" / "src",
    ]
    for path in paths:
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


def _fail(rule_id: str, evidence: str) -> DrillResult:
    return DrillResult(rule_id=rule_id, passed=False, evidence=evidence)


def _pass(rule_id: str) -> DrillResult:
    return DrillResult(rule_id=rule_id, passed=True, evidence=None)


def drill_identity_wallet_separation() -> DrillResult:
    _ensure_paths()
    from identity import Context, IdentityInputError, ERROR_WALLET_AS_IDENTITY, RootSecret, Identity

    sender_like = "0xdeadbeef"
    try:
        _ = Context(sender_like)
        return _fail("Q1-ID-02", "context accepted account-like sender")
    except IdentityInputError as exc:
        if exc.code != ERROR_WALLET_AS_IDENTITY:
            return _fail("Q1-ID-02", f"unexpected error code: {exc.code}")

    try:
        _ = Identity.create(sender_like, Context("ctx"))
        return _fail("Q1-ID-02", "identity accepted sender-like root secret")
    except IdentityInputError as exc:
        if exc.code != ERROR_WALLET_AS_IDENTITY:
            return _fail("Q1-ID-02", f"unexpected error code: {exc.code}")
    except Exception as exc:
        return _fail("Q1-ID-02", f"unexpected exception: {type(exc).__name__}")

    try:
        _ = RootSecret(sender_like)  # type: ignore[arg-type]
        return _fail("Q1-ID-02", "root secret accepted sender-like string")
    except IdentityInputError:
        pass

    return _pass("Q1-ID-02")


def drill_fee_free_action() -> DrillResult:
    _ensure_paths()
    from action import ActionDescriptor, ActionKind
    from engine import FeeEngineV0, FeeEngineError
    from fee import FeeComponentId, FeeError, FeeVector
    from quote import FeePayment

    action_descriptor = ActionDescriptor(
        kind=ActionKind.STATE_MUTATION,
        module="conformance",
        action="mutate",
        payload={"op": "set", "key": "k", "value": "v"},
    )

    try:
        _ = FeeVector.for_action(
            ActionKind.STATE_MUTATION,
            (
                (FeeComponentId.BASE, 0),
                (FeeComponentId.BYTES, 0),
                (FeeComponentId.COMPUTE, 0),
            ),
        )
        return _fail("Q1-FEE-01", "mutation accepted zero base fee")
    except FeeError:
        pass

    engine = FeeEngineV0()
    quote = engine.quote(action_descriptor, payer="payer")
    if quote.fee_vector.total() <= 0:
        return _fail("Q1-FEE-01", "fee total not positive")

    try:
        bad_vector = FeeVector.for_action(
            ActionKind.STATE_MUTATION,
            (
                (FeeComponentId.BASE, 1),
                (FeeComponentId.BYTES, 1),
                (FeeComponentId.COMPUTE, 1),
            ),
        )
        payment = FeePayment(
            payer=quote.payer,
            quote_hash=quote.quote_hash,
            paid_vector=bad_vector,
        )
        engine.enforce(quote, payment)
        return _fail("Q1-FEE-01", "enforce accepted mismatched paid vector")
    except FeeEngineError:
        pass

    return _pass("Q1-FEE-01")


def drill_fee_sponsor_amount() -> DrillResult:
    _ensure_paths()
    from action import ActionDescriptor, ActionKind
    from engine import FeeEngineV0, FeeEngineError
    from fee import FeeComponentId, FeeVector
    from quote import FeePayment

    action_descriptor = ActionDescriptor(
        kind=ActionKind.STATE_MUTATION,
        module="conformance",
        action="mutate",
        payload={"op": "set", "key": "k", "value": "v"},
    )
    engine = FeeEngineV0()
    quote = engine.quote(action_descriptor, payer="payer-a")
    sponsored = engine.sponsor(quote, "payer-b")
    if sponsored.fee_vector != quote.fee_vector:
        return _fail("Q1-FEE-02", "sponsor changed fee vector")

    try:
        lower_vector = FeeVector.for_action(
            ActionKind.STATE_MUTATION,
            (
                (FeeComponentId.BASE, 1),
                (FeeComponentId.BYTES, 0),
                (FeeComponentId.COMPUTE, 0),
            ),
        )
        payment = FeePayment(
            payer=quote.payer,
            quote_hash=quote.quote_hash,
            paid_vector=lower_vector,
        )
        engine.enforce(quote, payment)
        return _fail("Q1-FEE-02", "enforce accepted lower sponsor amount")
    except FeeEngineError:
        pass

    return _pass("Q1-FEE-02")


def drill_zk_context() -> tuple[DrillResult, DrillResult]:
    _ensure_paths()
    import hashlib
    from prover.mock import prove_mock
    from verifier import MockProofAdapter, verify
    from nullifier import compute_nullifier

    context_a = hashlib.sha256(b"ctx-a").digest()
    context_b = hashlib.sha256(b"ctx-b").digest()
    nonce = hashlib.sha256(b"nonce").digest()
    statement_id = "personhood.v0"

    envelope = prove_mock(
        statement_id=statement_id,
        context_id=context_a,
        nonce=nonce,
        public_inputs={"claim": True},
        witness={"secret": "value"},
    )
    adapter = MockProofAdapter()
    if verify(envelope, context_b, statement_id, adapter):
        return (
            _fail("Q1-ZK-01", "wrong context verified"),
            _pass("Q1-ZK-02"),
        )
    if not verify(envelope, context_a, statement_id, adapter):
        return (
            _fail("Q1-ZK-01", "correct context failed"),
            _pass("Q1-ZK-02"),
        )

    nullifier_a = compute_nullifier(
        context_id=context_a,
        statement_id=statement_id,
        epoch_or_nonce=nonce,
        secret_commitment=hashlib.sha256(b"commitment").digest(),
    )
    nullifier_b = compute_nullifier(
        context_id=context_b,
        statement_id=statement_id,
        epoch_or_nonce=nonce,
        secret_commitment=hashlib.sha256(b"commitment").digest(),
    )
    if nullifier_a == nullifier_b:
        return (
            _pass("Q1-ZK-01"),
            _fail("Q1-ZK-02", "nullifier reused across context"),
        )

    return (_pass("Q1-ZK-01"), _pass("Q1-ZK-02"))


def drill_root_secret_leak() -> DrillResult:
    _ensure_paths()
    from e2e_demo.hashing import sha256
    from e2e_demo.pipeline import run_e2e

    seed = 123
    root_secret = sha256(b"NYX:W7:ROOT:" + str(seed).encode("ascii"))
    secret_hex = root_secret.hex()

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        trace, summary = run_e2e(seed=seed)
    combined = buffer.getvalue() + trace.to_json() + repr(trace) + repr(summary)

    if secret_hex in combined:
        return _fail("Q1-SECRET-01", "root secret leaked in outputs")
    return _pass("Q1-SECRET-01")


def run_drills() -> tuple[DrillResult, ...]:
    results: list[DrillResult] = []
    results.append(drill_identity_wallet_separation())
    results.append(drill_fee_free_action())
    results.append(drill_fee_sponsor_amount())
    zk_results = drill_zk_context()
    results.extend(zk_results)
    results.append(drill_root_secret_leak())
    return tuple(results)
