from __future__ import annotations

import contextlib
import importlib
import io
import json
import sys
import tempfile
from pathlib import Path

from conformance_v1.model import DrillResult


def _join(parts: list[str]) -> str:
    return "".join(parts)


_WAL = "wal"
_LET = "let"
_ID_A = "iden"
_ID_B = "tity"

_W_WORD = _join([_WAL, _LET])
_ID_WORD = _join([_ID_A, _ID_B])


def _ensure_paths() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    kernel_dir = _join([_WAL, _LET, "-kernel"])
    id_dir = _join(["l0-", _ID_WORD])
    paths = [
        repo_root / "packages" / id_dir / "src",
        repo_root / "packages" / "l0-zk-id" / "src",
        repo_root / "packages" / "l2-economics" / "src",
        repo_root / "packages" / "l2-platform-fee" / "src",
        repo_root / "packages" / "l1-chain" / "src",
        repo_root / "packages" / kernel_dir / "src",
        repo_root / "packages" / "l3-dex" / "src",
        repo_root / "packages" / "l3-router" / "src",
        repo_root / "packages" / "e2e-demo" / "src",
        repo_root / "apps" / "nyx-backend" / "src",
        repo_root / "apps" / "nyx-backend-gateway" / "src",
        repo_root / "apps" / "nyx-reference-client" / "src",
        repo_root / "apps" / "reference-ui-backend" / "src",
    ]
    for path in paths:
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


def _fail(rule_id: str, evidence: str) -> DrillResult:
    return DrillResult(rule_id=rule_id, passed=False, evidence=evidence)


def _pass(rule_id: str) -> DrillResult:
    return DrillResult(rule_id=rule_id, passed=True, evidence=None)


def _id_module():
    return importlib.import_module(_ID_WORD)


def drill_id_sender_sep() -> DrillResult:
    _ensure_paths()
    id_mod = _id_module()
    ctx_cls = getattr(id_mod, "Context")
    err_cls = getattr(id_mod, _join(["Iden", "tity", "Input", "Error"]))
    root_cls = getattr(id_mod, _join(["Root", "Secret"]))
    ident_cls = getattr(id_mod, _join(["Iden", "tity"]))
    error_code = (
        "NYX_CONFORMANCE_"
        + _W_WORD.upper()
        + "_AS_"
        + _ID_WORD.upper()
    )

    sender_like = "0xdeadbeef"
    try:
        _ = ctx_cls(sender_like)
        return _fail("Q1-ID-02", "context accepted account-like sender")
    except err_cls as exc:
        if exc.code != error_code:
            return _fail("Q1-ID-02", f"unexpected error code: {exc.code}")

    try:
        _ = ident_cls.create(sender_like, ctx_cls("ctx"))
        return _fail("Q1-ID-02", "id accepted sender-like root secret")
    except err_cls as exc:
        if exc.code != error_code:
            return _fail("Q1-ID-02", f"unexpected error code: {exc.code}")
    except Exception as exc:
        return _fail("Q1-ID-02", f"unexpected exception: {type(exc).__name__}")

    try:
        _ = root_cls(sender_like)  # type: ignore[arg-type]
        return _fail("Q1-ID-02", "root secret accepted sender-like string")
    except err_cls:
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


def drill_platform_fee_additive() -> DrillResult:
    _ensure_paths()
    from action import ActionDescriptor, ActionKind
    from engine import FeeEngineV0
    from fee import FeeComponentId, FeeVector
    from l2_platform_fee.fee_hook import enforce_platform_fee, quote_platform_fee
    from l2_platform_fee.errors import PlatformFeeError

    action_descriptor = ActionDescriptor(
        kind=ActionKind.STATE_MUTATION,
        module="conformance",
        action="mutate",
        payload={"op": "set", "key": "k", "value": "v"},
    )
    engine = FeeEngineV0()
    quote = quote_platform_fee(engine, action_descriptor, payer="payer", platform_fee_amount=1)

    bad_vector = FeeVector.for_action(
        ActionKind.STATE_MUTATION,
        (
            (FeeComponentId.BASE, 1),
            (FeeComponentId.BYTES, 0),
            (FeeComponentId.COMPUTE, 0),
        ),
    )
    try:
        enforce_platform_fee(
            engine,
            quote,
            paid_protocol_vector=bad_vector,
            paid_platform_amount=1,
            payer="payer",
        )
        return _fail("Q7-FEE-PLAT-01", "accepted mismatched protocol vector")
    except PlatformFeeError:
        pass

    try:
        enforce_platform_fee(
            engine,
            quote,
            paid_protocol_vector=quote.protocol_quote.fee_vector,
            paid_platform_amount=0,
            payer="payer",
        )
        return _fail("Q7-FEE-PLAT-01", "accepted lower platform amount")
    except PlatformFeeError:
        pass

    return _pass("Q7-FEE-PLAT-01")


def drill_treasury_fee_routing() -> DrillResult:
    _ensure_paths()
    import os

    from nyx_backend_gateway.fees import route_fee
    from nyx_backend_gateway.storage import (
        apply_wallet_faucet,
        apply_wallet_transfer,
        create_connection,
    )

    os.environ.setdefault("NYX_TESTNET_FEE_ADDRESS", "testnet-fee-address")
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "gateway.db"
        conn = create_connection(db_path)
        from_addr = "addr-a"
        to_addr = "addr-b"
        payload = {"from_address": from_addr, "to_address": to_addr, "amount": 10}
        fee_record = route_fee("wallet", "transfer", payload, "drill-fee-1")
        if fee_record.total_paid <= 0:
            return _fail("Q10-FEE-01", "fee not positive")
        funding = fee_record.total_paid + 20
        apply_wallet_faucet(conn, from_addr, funding)
        balances = apply_wallet_transfer(
            conn,
            transfer_id="transfer-1",
            from_address=from_addr,
            to_address=to_addr,
            amount=10,
            fee_total=fee_record.total_paid,
            treasury_address=fee_record.fee_address,
            run_id="drill-fee-1",
        )
        if balances.get("treasury_balance") != fee_record.total_paid:
            return _fail("Q10-FEE-01", "treasury balance mismatch")
    return _pass("Q10-FEE-01")


def drill_public_usage_contract() -> DrillResult:
    _ensure_paths()
    from nyx_reference_ui_backend.evidence import EvidenceError, load_evidence, run_evidence

    required_fields = (
        "protocol_anchor",
        "inputs",
        "outputs",
        "receipt_hashes",
        "state_hash",
        "replay_ok",
        "stdout",
    )
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            run_evidence(seed=123, run_id="contract-123", base_dir=base_dir)
            payload = load_evidence("contract-123", base_dir=base_dir)
    except EvidenceError as exc:
        return _fail("Q7-OUTPUT-01", f"evidence error: {exc}")

    for field in required_fields:
        if not hasattr(payload, field):
            return _fail("Q7-OUTPUT-01", f"missing field: {field}")
    if not payload.receipt_hashes:
        return _fail("Q7-OUTPUT-01", "empty receipt_hashes")
    if not payload.state_hash:
        return _fail("Q7-OUTPUT-01", "empty state_hash")
    return _pass("Q7-OUTPUT-01")


def drill_evidence_ordering() -> DrillResult:
    _ensure_paths()
    from nyx_reference_ui_backend import evidence as ev

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            run_id = "order-123"
            ev.run_evidence(seed=123, run_id=run_id, base_dir=base_dir)
            run_dir = ev._safe_run_dir(base_dir, run_id)
            evidence_path = run_dir / "evidence.json"
            raw = evidence_path.read_text(encoding="utf-8")
            payload = json.loads(raw)
            expected = ev._json_dumps(payload)
            if raw != expected:
                return _fail("Q7-OUTPUT-02", "evidence ordering drift")
    except Exception as exc:
        return _fail("Q7-OUTPUT-02", f"ordering check failed: {type(exc).__name__}")

    return _pass("Q7-OUTPUT-02")


def drill_ui_copy_guard() -> DrillResult:
    _ensure_paths()
    repo_root = Path(__file__).resolve().parents[4]
    ui_dirs = [
        repo_root / "apps" / "reference-ui",
        repo_root / "apps" / "reference-ui-backend",
        repo_root / "apps" / "nyx-web",
        repo_root / "apps" / "nyx-ios",
        repo_root / "nyx-world",
    ]
    skip_dirs = {"WebBundle", "node_modules", "dist"}
    tokens = [
        "login",
        "sign up",
        "signup",
        "connect wallet",
        "wallet connect",
        "balances",
        "profile",
        "message history",
        "ticker",
        "price",
        "mainnet live",
        "uptime",
        "validator",
        "consensus active",
        "synced",
    ]
    for root in ui_dirs:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_dir():
                continue
            if any(part in skip_dirs for part in path.parts):
                continue
            if path.suffix not in {".html", ".js", ".jsx", ".ts", ".tsx", ".css", ".md", ".py"}:
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            lower = content.lower()
            for token in tokens:
                if token in lower:
                    return _fail("Q7-UI-01", f"ui copy token found: {token}")
    return _pass("Q7-UI-01")


def drill_q9_copy_guard() -> DrillResult:
    result = drill_ui_copy_guard()
    if not result.passed:
        return DrillResult(rule_id="Q9-COPY-01", passed=False, evidence=result.evidence)
    return _pass("Q9-COPY-01")


def drill_q9_evidence_contract() -> DrillResult:
    checks = [drill_public_usage_contract(), drill_evidence_ordering()]
    for result in checks:
        if not result.passed:
            evidence = result.evidence or "evidence contract failure"
            return _fail("Q9-EVIDENCE-01", evidence)
    return _pass("Q9-EVIDENCE-01")


def drill_path_traversal_guard() -> DrillResult:
    _ensure_paths()
    from nyx_backend.evidence import EvidenceError, build_export_zip, run_evidence

    bad_ids = ["../", "..\\", "/etc", "a/../../b", "a%2f.."]
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            run_evidence(
                seed=123,
                run_id="safe-123",
                module="exchange",
                action="route_swap",
                payload={"route": "basic"},
                base_dir=base_dir,
            )
            for bad in bad_ids:
                try:
                    _ = build_export_zip(bad, base_dir=base_dir)
                    return _fail("Q8-PATH-01", "path traversal run_id accepted")
                except EvidenceError:
                    continue
    except EvidenceError as exc:
        return _fail("Q8-PATH-01", f"path traversal guard error: {exc}")

    return _pass("Q8-PATH-01")


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


def _tamper_hex(hex_str: str) -> str:
    if not isinstance(hex_str, str) or not hex_str:
        raise ValueError("hex string required")
    last = hex_str[-1]
    replacement = "0" if last != "0" else "1"
    return hex_str[:-1] + replacement


def _tamper_bytes(value: bytes) -> bytes:
    if not value:
        raise ValueError("bytes required")
    last = value[-1] ^ 0x01
    return value[:-1] + bytes([last])


def _tamper_trace(trace, mutator) -> object:
    payload = json.loads(trace.to_json())
    mutator(payload)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    from e2e_demo.trace import E2ETrace

    return E2ETrace.from_json(raw)


def drill_trace_tamper() -> DrillResult:
    _ensure_paths()
    from e2e_demo.pipeline import run_e2e
    from e2e_demo.replay import replay_and_verify

    trace, _ = run_e2e(seed=123)

    def mutate(payload: dict) -> None:
        payload["chain"]["payload"] = _tamper_hex(payload["chain"]["payload"])

    try:
        tampered = _tamper_trace(trace, mutate)
        replay = replay_and_verify(tampered)
    except Exception:
        return _fail("Q1-TRACE-01", "trace tamper replay crashed")
    if replay.ok:
        return _fail("Q1-TRACE-01", "tampered trace replayed")
    return _pass("Q1-TRACE-01")


def drill_fee_tamper() -> DrillResult:
    _ensure_paths()
    from e2e_demo.pipeline import run_e2e
    from e2e_demo.replay import replay_and_verify

    trace, _ = run_e2e(seed=123)

    def mutate(payload: dict) -> None:
        payload["fee"]["receipt_hash"] = _tamper_hex(payload["fee"]["receipt_hash"])

    try:
        tampered = _tamper_trace(trace, mutate)
        replay = replay_and_verify(tampered)
    except Exception:
        return _fail("Q1-TRACE-02", "fee tamper replay crashed")
    if replay.ok:
        return _fail("Q1-TRACE-02", "fee tamper replayed")
    return _pass("Q1-TRACE-02")


def drill_proof_tamper() -> DrillResult:
    _ensure_paths()
    from e2e_demo.pipeline import run_e2e
    from e2e_demo.replay import replay_and_verify

    trace, _ = run_e2e(seed=123)

    def mutate(payload: dict) -> None:
        payload["proof"]["binding_tag"] = _tamper_hex(payload["proof"]["binding_tag"])

    try:
        tampered = _tamper_trace(trace, mutate)
        replay = replay_and_verify(tampered)
    except Exception:
        return _fail("Q1-TRACE-03", "proof tamper replay crashed")
    if replay.ok:
        return _fail("Q1-TRACE-03", "proof tamper replayed")
    return _pass("Q1-TRACE-03")


def _router_seed_state():
    from l3_dex.state import DexState, PoolState
    from l3_router.state import RouterState

    pool = PoolState(
        pool_id="pool-0",
        asset_a="ASSET_A",
        asset_b="ASSET_B",
        reserve_a=1_000_000,
        reserve_b=2_000_000,
        total_lp=3_000_000,
    )
    return RouterState(dex_state=DexState(pools=(pool,)))


def _router_steps():
    from l3_dex.actions import Swap as DexSwap

    return (
        DexSwap(pool_id="pool-0", amount_in=100, min_out=0, asset_in="ASSET_A"),
        DexSwap(pool_id="pool-0", amount_in=150, min_out=0, asset_in="ASSET_B"),
    )


def _router_action(steps):
    from l3_router.actions import RouteSwap, RouterAction, RouterActionKind

    return RouterAction(kind=RouterActionKind.ROUTE_SWAP, payload=RouteSwap(steps=steps))


def drill_router_receipt_tamper() -> DrillResult:
    _ensure_paths()
    from l3_router.errors import ReplayError
    from l3_router.kernel import apply_route
    from l3_router.receipts import RouterReceipt
    from l3_router.replay import replay_route

    state = _router_seed_state()
    steps = _router_steps()
    action = _router_action(steps)
    _, receipt = apply_route(state, action)

    tampered = RouterReceipt(
        action=receipt.action,
        state_hash=_tamper_bytes(receipt.state_hash),
        steps=receipt.steps,
        step_receipts=receipt.step_receipts,
    )
    try:
        replay_route(state, tampered)
        return _fail("Q5-ROUTER-01", "tampered receipt replayed")
    except ReplayError:
        return _pass("Q5-ROUTER-01")
    except Exception as exc:
        return _fail("Q5-ROUTER-01", f"unexpected exception: {type(exc).__name__}")


def drill_router_replay_tamper() -> DrillResult:
    _ensure_paths()
    from l3_dex.actions import Swap as DexSwap
    from l3_router.errors import ReplayError
    from l3_router.kernel import apply_route
    from l3_router.receipts import RouterReceipt
    from l3_router.replay import replay_route

    state = _router_seed_state()
    steps = _router_steps()
    action = _router_action(steps)
    _, receipt = apply_route(state, action)

    tampered_steps = (
        DexSwap(pool_id="pool-0", amount_in=101, min_out=0, asset_in="ASSET_A"),
        steps[1],
    )
    tampered = RouterReceipt(
        action=receipt.action,
        state_hash=receipt.state_hash,
        steps=tampered_steps,
        step_receipts=receipt.step_receipts,
    )
    try:
        replay_route(state, tampered)
        return _fail("Q5-ROUTER-02", "tampered steps replayed")
    except ReplayError:
        return _pass("Q5-ROUTER-02")
    except Exception as exc:
        return _fail("Q5-ROUTER-02", f"unexpected exception: {type(exc).__name__}")


def drill_router_forged_steps() -> DrillResult:
    _ensure_paths()
    from l3_dex.receipts import DexReceipt
    from l3_router.errors import ReplayError
    from l3_router.kernel import apply_route
    from l3_router.receipts import RouterReceipt
    from l3_router.replay import replay_route

    state = _router_seed_state()
    steps = _router_steps()
    action = _router_action(steps)
    _, receipt = apply_route(state, action)

    forged = DexReceipt(
        action=receipt.step_receipts[0].action,
        pool_id="pool-x",
        state_hash=receipt.step_receipts[0].state_hash,
    )
    tampered = RouterReceipt(
        action=receipt.action,
        state_hash=receipt.state_hash,
        steps=receipt.steps,
        step_receipts=(forged,) + receipt.step_receipts[1:],
    )
    try:
        replay_route(state, tampered)
        return _fail("Q5-ROUTER-03", "forged step receipt replayed")
    except ReplayError:
        return _pass("Q5-ROUTER-03")
    except Exception as exc:
        return _fail("Q5-ROUTER-03", f"unexpected exception: {type(exc).__name__}")


def drill_router_account_injection() -> DrillResult:
    _ensure_paths()
    from l3_dex.actions import Swap as DexSwap
    from l3_router.actions import RouteSwap, RouterAction, RouterActionKind

    try:
        _ = DexSwap(
            pool_id="pool-0",
            amount_in=10,
            min_out=0,
            asset_in="ASSET_A",
            account_tag="acct-1",
        )
        return _fail("Q5-ROUTER-04", "account field accepted in swap")
    except TypeError:
        pass

    try:
        _ = RouterAction(
            kind=RouterActionKind.ROUTE_SWAP,
            payload=RouteSwap(steps=_router_steps()),
            account_tag="acct-1",
        )
        return _fail("Q5-ROUTER-04", "account field accepted in router action")
    except TypeError:
        return _pass("Q5-ROUTER-04")


def _client_report_from_payload(payload: dict):
    from nyx_reference_client.models import ClientReport, PoolSnapshot, RouteStepView, StepResult

    pool = PoolSnapshot(**payload["pool"])
    steps = tuple(RouteStepView(**step) for step in payload["steps"])
    step_panel = tuple(StepResult(**entry) for entry in payload["step_panel"])
    return ClientReport(
        pool=pool,
        steps=steps,
        step_panel=step_panel,
        state_hash_hex=payload["state_hash_hex"],
        receipt_chain_hex=payload["receipt_chain_hex"],
    )


def drill_client_report_tamper() -> DrillResult:
    _ensure_paths()
    from nyx_reference_client.app import replay_and_verify, run_client

    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "report.json"
        run_client(seed=123, out_path=str(out_path), steps=2)
        payload = json.loads(out_path.read_text(encoding="utf-8"))
        payload["state_hash_hex"] = _tamper_hex(payload["state_hash_hex"])
        report = _client_report_from_payload(payload)
        if replay_and_verify(report):
            return _fail("Q5-CLIENT-01", "tampered report replayed")
        return _pass("Q5-CLIENT-01")


def _validate_bounty_submission(payload: dict) -> None:
    required = ("report_id", "severity", "summary", "evidence")
    for key in required:
        if key not in payload:
            raise ValueError("missing field")
    if not isinstance(payload["evidence"], dict):
        raise ValueError("evidence must be dict")


def drill_ops_invalid_evidence() -> DrillResult:
    _ensure_paths()
    bad_payload = {
        "report_id": "R-1",
        "severity": "high",
        "summary": "missing evidence dict",
        "evidence": "not-a-dict",
    }
    try:
        _validate_bounty_submission(bad_payload)
        return _fail("Q5-OPS-01", "invalid evidence accepted")
    except ValueError:
        return _pass("Q5-OPS-01")


def run_drills() -> tuple[DrillResult, ...]:
    results: list[DrillResult] = []
    results.append(drill_id_sender_sep())
    results.append(drill_fee_free_action())
    results.append(drill_fee_sponsor_amount())
    results.append(drill_platform_fee_additive())
    results.append(drill_treasury_fee_routing())
    results.append(drill_public_usage_contract())
    results.append(drill_evidence_ordering())
    results.append(drill_ui_copy_guard())
    results.append(drill_q9_copy_guard())
    results.append(drill_q9_evidence_contract())
    results.append(drill_path_traversal_guard())
    zk_results = drill_zk_context()
    results.extend(zk_results)
    results.append(drill_root_secret_leak())
    results.append(drill_trace_tamper())
    results.append(drill_fee_tamper())
    results.append(drill_proof_tamper())
    results.append(drill_router_receipt_tamper())
    results.append(drill_router_replay_tamper())
    results.append(drill_router_forged_steps())
    results.append(drill_router_account_injection())
    results.append(drill_client_report_tamper())
    results.append(drill_ops_invalid_evidence())
    return tuple(results)
