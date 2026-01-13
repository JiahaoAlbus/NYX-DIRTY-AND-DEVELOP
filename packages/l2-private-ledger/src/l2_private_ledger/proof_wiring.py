from __future__ import annotations

from typing import Any

from l2_private_ledger.actions import ActionKind, LedgerAction, PrivateMint, PrivateSpend
from l2_private_ledger.errors import ValidationError
from l2_private_ledger.state import LedgerState, state_root
from l2_private_ledger.types import compare_digest, ensure_bytes32, framed, sha256

try:
    from canonical import CanonicalizationError, canonicalize
    from envelope import ProofEnvelope
    from prover.mock import prove_mock
    from verifier import MockProofAdapter, verify as verify_envelope
except Exception as exc:  # pragma: no cover - handled at runtime
    ProofEnvelope = None  # type: ignore
    MockProofAdapter = object  # type: ignore
    _IMPORT_ERROR = exc

    def _missing(*_args, **_kwargs):
        raise ValidationError("l0-zk-id unavailable") from _IMPORT_ERROR

    canonicalize = _missing  # type: ignore
    prove_mock = _missing  # type: ignore
    verify_envelope = _missing  # type: ignore
    CanonicalizationError = ValidationError  # type: ignore


DEFAULT_CONTEXT_ID = sha256(b"NYX:CTX:Q3:PRIVATE_LEDGER:v1")
DEFAULT_STATEMENT_ID = "NYX:STATEMENT:PRIVATE_LEDGER_ACTION:v1"


def compute_action_hash(action: LedgerAction) -> bytes:
    if not isinstance(action, LedgerAction):
        raise ValidationError("action must be LedgerAction")
    if action.kind == ActionKind.PRIVATE_MINT:
        payload = action.payload
        assert isinstance(payload, PrivateMint)
        payload_bytes = ensure_bytes32(payload.commitment, "commitment")
    elif action.kind == ActionKind.PRIVATE_SPEND:
        payload = action.payload
        assert isinstance(payload, PrivateSpend)
        payload_bytes = ensure_bytes32(payload.nullifier, "nullifier")
    else:
        raise ValidationError("unsupported action kind")
    kind_bytes = action.kind.value.encode("utf-8")
    action_hash = sha256(
        framed([b"NYX:PL:ACTION_HASH:v1", kind_bytes, payload_bytes])
    )
    ensure_bytes32(action_hash, "action_hash")
    return action_hash


def build_public_inputs(
    ledger_root: bytes,
    action: LedgerAction,
    action_hash: bytes,
) -> dict[str, object]:
    ledger_root_bytes = ensure_bytes32(ledger_root, "ledger_root")
    action_hash_bytes = ensure_bytes32(action_hash, "action_hash")
    if not isinstance(action, LedgerAction):
        raise ValidationError("action must be LedgerAction")
    payload: dict[str, str]
    if action.kind == ActionKind.PRIVATE_MINT:
        payload_obj = action.payload
        assert isinstance(payload_obj, PrivateMint)
        payload = {"commitment": payload_obj.commitment.hex()}
    elif action.kind == ActionKind.PRIVATE_SPEND:
        payload_obj = action.payload
        assert isinstance(payload_obj, PrivateSpend)
        payload = {"nullifier": payload_obj.nullifier.hex()}
    else:
        raise ValidationError("unsupported action kind")
    return {
        "ledger_root": ledger_root_bytes.hex(),
        "action_hash": action_hash_bytes.hex(),
        "action_kind": action.kind.value,
        "payload": payload,
        "v": 1,
    }


def validate_public_inputs_shape(public_inputs: dict[str, object]) -> None:
    if not isinstance(public_inputs, dict):
        raise ValidationError("public_inputs must be dict")
    _validate_jsonlike(public_inputs)
    try:
        canonicalize(public_inputs)
    except CanonicalizationError as exc:
        raise ValidationError(str(exc)) from exc

    required = {"ledger_root", "action_hash", "action_kind", "payload", "v"}
    missing = [key for key in required if key not in public_inputs]
    if missing:
        raise ValidationError("public_inputs missing required fields")

    if not isinstance(public_inputs.get("action_kind"), str):
        raise ValidationError("action_kind must be string")
    if not isinstance(public_inputs.get("payload"), dict):
        raise ValidationError("payload must be dict")
    if not isinstance(public_inputs.get("v"), int) or isinstance(
        public_inputs.get("v"), bool
    ):
        raise ValidationError("v must be int")
    if public_inputs.get("v") != 1:
        raise ValidationError("v must be 1")

    _require_hex_bytes32("ledger_root", public_inputs.get("ledger_root"))
    _require_hex_bytes32("action_hash", public_inputs.get("action_hash"))

    payload = public_inputs.get("payload")
    assert isinstance(payload, dict)
    if not payload:
        raise ValidationError("payload must not be empty")
    for key, value in payload.items():
        if not isinstance(key, str):
            raise ValidationError("payload keys must be strings")
        if key not in {"commitment", "nullifier"}:
            raise ValidationError("payload key not allowed")
        _require_hex_bytes32(key, value)


def prove_private_action_mock(
    state: LedgerState,
    action: LedgerAction,
    nonce: bytes,
    witness: object,
    *,
    context_id: bytes = DEFAULT_CONTEXT_ID,
    statement_id: str = DEFAULT_STATEMENT_ID,
) -> ProofEnvelope:
    if ProofEnvelope is None:
        raise ValidationError("l0-zk-id unavailable")
    if not isinstance(state, LedgerState):
        raise ValidationError("state must be LedgerState")
    ensure_bytes32(context_id, "context_id")
    ensure_bytes32(nonce, "nonce")
    if not isinstance(statement_id, str) or not statement_id:
        raise ValidationError("statement_id must be non-empty string")

    root = state_root(state)
    action_hash = compute_action_hash(action)
    public_inputs = build_public_inputs(root, action, action_hash)
    validate_public_inputs_shape(public_inputs)
    return prove_mock(
        statement_id=statement_id,
        context_id=context_id,
        nonce=nonce,
        public_inputs=public_inputs,
        witness=witness,
    )


def verify_private_action(
    envelope: ProofEnvelope,
    expected_state_root: bytes,
    expected_action: LedgerAction,
    *,
    context_id: bytes = DEFAULT_CONTEXT_ID,
    statement_id: str = DEFAULT_STATEMENT_ID,
    verifier_adapter: object | None = None,
) -> bool:
    if ProofEnvelope is None:
        return False
    if not isinstance(envelope, ProofEnvelope):
        return False
    try:
        expected_root = ensure_bytes32(expected_state_root, "expected_state_root")
        ensure_bytes32(context_id, "context_id")
    except ValidationError:
        return False
    if not isinstance(statement_id, str) or not statement_id:
        return False
    if not isinstance(expected_action, LedgerAction):
        return False

    try:
        validate_public_inputs_shape(envelope.public_inputs)
    except ValidationError:
        return False

    public_inputs = envelope.public_inputs
    try:
        ledger_root = _require_hex_bytes32("ledger_root", public_inputs.get("ledger_root"))
        action_hash = _require_hex_bytes32("action_hash", public_inputs.get("action_hash"))
    except ValidationError:
        return False

    if not compare_digest(ledger_root, expected_root):
        return False
    expected_hash = compute_action_hash(expected_action)
    if not compare_digest(action_hash, expected_hash):
        return False

    if public_inputs.get("action_kind") != expected_action.kind.value:
        return False
    payload = public_inputs.get("payload")
    if not isinstance(payload, dict):
        return False
    expected_key, expected_value = _expected_payload(expected_action)
    if set(payload.keys()) != {expected_key}:
        return False
    try:
        payload_bytes = _require_hex_bytes32(expected_key, payload.get(expected_key))
    except ValidationError:
        return False
    if not compare_digest(payload_bytes, expected_value):
        return False

    if public_inputs.get("v") != 1:
        return False

    adapter = verifier_adapter if verifier_adapter is not None else MockProofAdapter()
    try:
        return bool(verify_envelope(envelope, context_id, statement_id, adapter))
    except Exception:
        return False


def _expected_payload(action: LedgerAction) -> tuple[str, bytes]:
    if action.kind == ActionKind.PRIVATE_MINT:
        payload = action.payload
        assert isinstance(payload, PrivateMint)
        return "commitment", ensure_bytes32(payload.commitment, "commitment")
    payload = action.payload
    assert isinstance(payload, PrivateSpend)
    return "nullifier", ensure_bytes32(payload.nullifier, "nullifier")


def _require_hex_bytes32(name: str, value: object) -> bytes:
    if not isinstance(value, str):
        raise ValidationError(f"{name} must be hex string")
    if len(value) != 64:
        raise ValidationError(f"{name} must be 32-byte hex")
    try:
        raw = bytes.fromhex(value)
    except ValueError as exc:
        raise ValidationError(f"{name} must be hex") from exc
    return ensure_bytes32(raw, name)


def _validate_jsonlike(value: object) -> None:
    if value is None:
        return
    if isinstance(value, bool):
        return
    if isinstance(value, int) and not isinstance(value, bool):
        return
    if isinstance(value, str):
        _reject_surrogates(value)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _validate_jsonlike(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValidationError("dict keys must be strings")
            _reject_surrogates(key)
            _validate_jsonlike(item)
        return
    if isinstance(value, float):
        raise ValidationError("float values are not permitted")
    if isinstance(value, (bytes, bytearray)):
        raise ValidationError("byte values are not permitted")
    if isinstance(value, set):
        raise ValidationError("set values are not permitted")
    raise ValidationError("unsupported type")


def _reject_surrogates(text: str) -> None:
    for char in text:
        code = ord(char)
        if 0xD800 <= code <= 0xDFFF:
            raise ValidationError("surrogate code points are not permitted")
