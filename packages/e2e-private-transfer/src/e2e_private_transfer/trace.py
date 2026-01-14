from __future__ import annotations

import json
from dataclasses import dataclass

from e2e_private_transfer.canonical import CanonicalizationError, canonicalize, require_text
from e2e_private_transfer.hashing import HashingError, bytes32_hex, hex_to_bytes32


class TraceError(ValueError):
    pass


@dataclass(frozen=True)
class IdentityTrace:
    commitment_hex: str

    def __post_init__(self) -> None:
        try:
            hex_to_bytes32(self.commitment_hex, "commitment_hex")
        except HashingError as exc:
            raise TraceError(str(exc)) from exc


@dataclass(frozen=True)
class ProofEnvelopeTrace:
    protocol_version: str
    statement_id: str
    context_id_hex: str
    nonce_hex: str
    public_inputs: dict
    proof_bytes_hex: str
    binding_tag_hex: str
    nullifier_hex: str | None

    def __post_init__(self) -> None:
        try:
            require_text(self.protocol_version, "protocol_version")
            require_text(self.statement_id, "statement_id")
        except CanonicalizationError as exc:
            raise TraceError(str(exc)) from exc
        try:
            hex_to_bytes32(self.context_id_hex, "context_id")
            hex_to_bytes32(self.nonce_hex, "nonce")
            hex_to_bytes32(self.binding_tag_hex, "binding_tag")
        except HashingError as exc:
            raise TraceError(str(exc)) from exc
        if self.nullifier_hex is not None:
            try:
                hex_to_bytes32(self.nullifier_hex, "nullifier")
            except HashingError as exc:
                raise TraceError(str(exc)) from exc
        if not isinstance(self.proof_bytes_hex, str):
            raise TraceError("proof_bytes must be hex string")
        try:
            bytes.fromhex(self.proof_bytes_hex)
        except ValueError as exc:
            raise TraceError("proof_bytes must be hex") from exc
        if not isinstance(self.public_inputs, dict):
            raise TraceError("public_inputs must be dict")
        try:
            canonicalize(self.public_inputs)
        except CanonicalizationError as exc:
            raise TraceError(str(exc)) from exc

    def to_envelope(self):
        try:
            from envelope import ProofEnvelope
        except Exception as exc:  # pragma: no cover
            raise TraceError("l0-zk-id unavailable") from exc
        return ProofEnvelope(
            protocol_version=self.protocol_version,
            statement_id=self.statement_id,
            context_id=hex_to_bytes32(self.context_id_hex, "context_id"),
            nonce=hex_to_bytes32(self.nonce_hex, "nonce"),
            public_inputs=self.public_inputs,
            proof_bytes=bytes.fromhex(self.proof_bytes_hex),
            binding_tag=hex_to_bytes32(self.binding_tag_hex, "binding_tag"),
            nullifier=(
                None
                if self.nullifier_hex is None
                else hex_to_bytes32(self.nullifier_hex, "nullifier")
            ),
        )

    @classmethod
    def from_envelope(cls, envelope) -> "ProofEnvelopeTrace":
        return cls(
            protocol_version=envelope.protocol_version,
            statement_id=envelope.statement_id,
            context_id_hex=bytes32_hex(envelope.context_id, "context_id"),
            nonce_hex=bytes32_hex(envelope.nonce, "nonce"),
            public_inputs=envelope.public_inputs,
            proof_bytes_hex=envelope.proof_bytes.hex(),
            binding_tag_hex=bytes32_hex(envelope.binding_tag, "binding_tag"),
            nullifier_hex=(
                None if envelope.nullifier is None else bytes32_hex(envelope.nullifier, "nullifier")
            ),
        )


@dataclass(frozen=True)
class SanityTrace:
    wrong_context_failed: bool

    def __post_init__(self) -> None:
        if not isinstance(self.wrong_context_failed, bool):
            raise TraceError("wrong_context_failed must be bool")


@dataclass(frozen=True)
class PrivateActionTrace:
    kind: str
    payload: dict
    ledger_root_hex: str
    action_hash_hex: str

    def __post_init__(self) -> None:
        try:
            require_text(self.kind, "kind")
        except CanonicalizationError as exc:
            raise TraceError(str(exc)) from exc
        if not isinstance(self.payload, dict):
            raise TraceError("payload must be dict")
        try:
            canonicalize(self.payload)
        except CanonicalizationError as exc:
            raise TraceError(str(exc)) from exc
        try:
            hex_to_bytes32(self.ledger_root_hex, "ledger_root")
            hex_to_bytes32(self.action_hash_hex, "action_hash")
        except HashingError as exc:
            raise TraceError(str(exc)) from exc


@dataclass(frozen=True)
class FeeTrace:
    payer: str
    components: list[dict[str, object]]
    total: int
    quote_hash_hex: str
    receipt_hash_hex: str
    sponsor_same_amount: bool

    def __post_init__(self) -> None:
        try:
            require_text(self.payer, "payer")
        except CanonicalizationError as exc:
            raise TraceError(str(exc)) from exc
        if not isinstance(self.components, list):
            raise TraceError("components must be list")
        try:
            canonicalize(self.components)
        except CanonicalizationError as exc:
            raise TraceError(str(exc)) from exc
        if not isinstance(self.total, int) or isinstance(self.total, bool):
            raise TraceError("total must be int")
        try:
            hex_to_bytes32(self.quote_hash_hex, "quote_hash")
            hex_to_bytes32(self.receipt_hash_hex, "receipt_hash")
        except HashingError as exc:
            raise TraceError(str(exc)) from exc
        if not isinstance(self.sponsor_same_amount, bool):
            raise TraceError("sponsor_same_amount must be bool")


@dataclass(frozen=True)
class StateProofTrace:
    key_hex: str
    value_hex: str | None
    state_root_hex: str
    proof_bytes_hex: str

    def __post_init__(self) -> None:
        if not isinstance(self.key_hex, str):
            raise TraceError("key_hex must be str")
        try:
            bytes.fromhex(self.key_hex)
        except ValueError as exc:
            raise TraceError("key_hex must be hex") from exc
        if self.value_hex is not None:
            if not isinstance(self.value_hex, str):
                raise TraceError("value_hex must be str")
            try:
                bytes.fromhex(self.value_hex)
            except ValueError as exc:
                raise TraceError("value_hex must be hex") from exc
        try:
            hex_to_bytes32(self.state_root_hex, "state_root")
        except HashingError as exc:
            raise TraceError(str(exc)) from exc
        if not isinstance(self.proof_bytes_hex, str):
            raise TraceError("proof_bytes must be hex string")
        try:
            bytes.fromhex(self.proof_bytes_hex)
        except ValueError as exc:
            raise TraceError("proof_bytes must be hex") from exc


@dataclass(frozen=True)
class ChainTrace:
    chain_id: str
    sender: str
    nonce_hex: str
    payload_hex: str
    signature_hex: str
    tx_hash_hex: str
    block_height: int
    block_hash_hex: str
    state_root_before_hex: str
    state_root_after_hex: str
    finality_proof_hex: str
    state_proof: StateProofTrace

    def __post_init__(self) -> None:
        try:
            require_text(self.chain_id, "chain_id")
            require_text(self.sender, "sender")
        except CanonicalizationError as exc:
            raise TraceError(str(exc)) from exc
        for name, value in (
            ("nonce_hex", self.nonce_hex),
            ("payload_hex", self.payload_hex),
            ("signature_hex", self.signature_hex),
            ("tx_hash_hex", self.tx_hash_hex),
            ("block_hash_hex", self.block_hash_hex),
            ("state_root_before_hex", self.state_root_before_hex),
            ("state_root_after_hex", self.state_root_after_hex),
            ("finality_proof_hex", self.finality_proof_hex),
        ):
            if not isinstance(value, str):
                raise TraceError(f"{name} must be str")
            try:
                bytes.fromhex(value)
            except ValueError as exc:
                raise TraceError(f"{name} must be hex") from exc
        if not isinstance(self.block_height, int) or isinstance(self.block_height, bool):
            raise TraceError("block_height must be int")
        if not isinstance(self.state_proof, StateProofTrace):
            raise TraceError("state_proof must be StateProofTrace")


@dataclass(frozen=True)
class TransferTrace:
    identity: IdentityTrace
    action: PrivateActionTrace
    proof: ProofEnvelopeTrace
    fee: FeeTrace
    chain: ChainTrace
    sanity: SanityTrace

    def __post_init__(self) -> None:
        if not isinstance(self.identity, IdentityTrace):
            raise TraceError("identity must be IdentityTrace")
        if not isinstance(self.action, PrivateActionTrace):
            raise TraceError("action must be PrivateActionTrace")
        if not isinstance(self.proof, ProofEnvelopeTrace):
            raise TraceError("proof must be ProofEnvelopeTrace")
        if not isinstance(self.fee, FeeTrace):
            raise TraceError("fee must be FeeTrace")
        if not isinstance(self.chain, ChainTrace):
            raise TraceError("chain must be ChainTrace")
        if not isinstance(self.sanity, SanityTrace):
            raise TraceError("sanity must be SanityTrace")

    def to_dict(self) -> dict[str, object]:
        return {
            "identity": self.identity.__dict__,
            "action": self.action.__dict__,
            "proof": self.proof.__dict__,
            "fee": self.fee.__dict__,
            "chain": {
                **self.chain.__dict__,
                "state_proof": self.chain.state_proof.__dict__,
            },
            "sanity": self.sanity.__dict__,
        }

    def to_json(self) -> str:
        payload = self.to_dict()
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "TransferTrace":
        if not isinstance(payload, dict):
            raise TraceError("trace payload must be dict")
        try:
            identity = IdentityTrace(**payload["identity"])
            action = PrivateActionTrace(**payload["action"])
            proof = ProofEnvelopeTrace(**payload["proof"])
            chain_payload = payload["chain"]
            state_proof = StateProofTrace(**chain_payload["state_proof"])
            chain = ChainTrace(
                **{k: v for k, v in chain_payload.items() if k != "state_proof"},
                state_proof=state_proof,
            )
            fee = FeeTrace(**payload["fee"])
            sanity = SanityTrace(**payload["sanity"])
        except KeyError as exc:
            raise TraceError("trace payload missing field") from exc
        return cls(
            identity=identity,
            action=action,
            proof=proof,
            fee=fee,
            chain=chain,
            sanity=sanity,
        )

    @classmethod
    def from_json(cls, raw: str) -> "TransferTrace":
        if not isinstance(raw, str):
            raise TraceError("trace json must be string")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise TraceError("trace json must be valid") from exc
        return cls.from_dict(payload)
