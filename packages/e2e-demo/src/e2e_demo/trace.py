from __future__ import annotations

import json
from dataclasses import dataclass

from e2e_demo.canonical import CanonicalizationError, canonicalize, require_text
from e2e_demo.hashing import HashingError, bytes32_hex, hex_to_bytes32


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
    wrong_context_verified: bool
    correct_context_verified: bool

    def __post_init__(self) -> None:
        if not isinstance(self.wrong_context_verified, bool):
            raise TraceError("wrong_context_verified must be bool")
        if not isinstance(self.correct_context_verified, bool):
            raise TraceError("correct_context_verified must be bool")


@dataclass(frozen=True)
class ActionTrace:
    kind: str
    module: str
    action: str
    payload: dict
    metadata: dict | None
    action_hash_hex: str

    def __post_init__(self) -> None:
        try:
            require_text(self.kind, "kind")
            require_text(self.module, "module")
            require_text(self.action, "action")
        except CanonicalizationError as exc:
            raise TraceError(str(exc)) from exc
        if not isinstance(self.payload, dict):
            raise TraceError("payload must be dict")
        try:
            canonicalize(self.payload)
        except CanonicalizationError as exc:
            raise TraceError(str(exc)) from exc
        if self.metadata is not None:
            if not isinstance(self.metadata, dict):
                raise TraceError("metadata must be dict")
            try:
                canonicalize(self.metadata)
            except CanonicalizationError as exc:
                raise TraceError(str(exc)) from exc
        try:
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
            raise TraceError("proof_bytes must be hex")
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
        try:
            hex_to_bytes32(self.nonce_hex, "nonce")
            hex_to_bytes32(self.tx_hash_hex, "tx_hash")
            hex_to_bytes32(self.block_hash_hex, "block_hash")
            hex_to_bytes32(self.state_root_before_hex, "state_root_before")
            hex_to_bytes32(self.state_root_after_hex, "state_root_after")
        except HashingError as exc:
            raise TraceError(str(exc)) from exc
        for field_name, value in (
            ("payload_hex", self.payload_hex),
            ("signature_hex", self.signature_hex),
            ("finality_proof_hex", self.finality_proof_hex),
        ):
            if not isinstance(value, str):
                raise TraceError(f"{field_name} must be str")
            try:
                bytes.fromhex(value)
            except ValueError as exc:
                raise TraceError(f"{field_name} must be hex") from exc
        if not isinstance(self.block_height, int) or isinstance(self.block_height, bool):
            raise TraceError("block_height must be int")
        if self.block_height < 0:
            raise TraceError("block_height must be >= 0")
        if not isinstance(self.state_proof, StateProofTrace):
            raise TraceError("state_proof must be StateProofTrace")


@dataclass(frozen=True)
class E2ETrace:
    identity: IdentityTrace
    proof: ProofEnvelopeTrace
    sanity: SanityTrace
    action: ActionTrace
    fee: FeeTrace
    chain: ChainTrace

    def __post_init__(self) -> None:
        if not isinstance(self.identity, IdentityTrace):
            raise TraceError("identity must be IdentityTrace")
        if not isinstance(self.proof, ProofEnvelopeTrace):
            raise TraceError("proof must be ProofEnvelopeTrace")
        if not isinstance(self.sanity, SanityTrace):
            raise TraceError("sanity must be SanityTrace")
        if not isinstance(self.action, ActionTrace):
            raise TraceError("action must be ActionTrace")
        if not isinstance(self.fee, FeeTrace):
            raise TraceError("fee must be FeeTrace")
        if not isinstance(self.chain, ChainTrace):
            raise TraceError("chain must be ChainTrace")

    def to_dict(self) -> dict:
        payload = {
            "identity": {"commitment": self.identity.commitment_hex},
            "proof": {
                "protocol_version": self.proof.protocol_version,
                "statement_id": self.proof.statement_id,
                "context_id": self.proof.context_id_hex,
                "nonce": self.proof.nonce_hex,
                "public_inputs": self.proof.public_inputs,
                "proof_bytes": self.proof.proof_bytes_hex,
                "binding_tag": self.proof.binding_tag_hex,
                "nullifier": self.proof.nullifier_hex,
            },
            "sanity": {
                "wrong_context_verified": self.sanity.wrong_context_verified,
                "correct_context_verified": self.sanity.correct_context_verified,
            },
            "action": {
                "kind": self.action.kind,
                "module": self.action.module,
                "action": self.action.action,
                "payload": self.action.payload,
                "metadata": self.action.metadata,
                "action_hash": self.action.action_hash_hex,
            },
            "fee": {
                "payer": self.fee.payer,
                "components": self.fee.components,
                "total": self.fee.total,
                "quote_hash": self.fee.quote_hash_hex,
                "receipt_hash": self.fee.receipt_hash_hex,
            },
            "chain": {
                "chain_id": self.chain.chain_id,
                "sender": self.chain.sender,
                "nonce": self.chain.nonce_hex,
                "payload": self.chain.payload_hex,
                "signature": self.chain.signature_hex,
                "tx_hash": self.chain.tx_hash_hex,
                "block_height": self.chain.block_height,
                "block_hash": self.chain.block_hash_hex,
                "state_root_before": self.chain.state_root_before_hex,
                "state_root_after": self.chain.state_root_after_hex,
                "finality_proof": self.chain.finality_proof_hex,
                "state_proof": {
                    "key": self.chain.state_proof.key_hex,
                    "value": self.chain.state_proof.value_hex,
                    "state_root": self.chain.state_proof.state_root_hex,
                    "proof_bytes": self.chain.state_proof.proof_bytes_hex,
                },
            },
        }
        try:
            canonicalize(payload)
        except CanonicalizationError as exc:
            raise TraceError(str(exc)) from exc
        return payload

    def to_json(self) -> str:
        payload = self.to_dict()
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: str) -> "E2ETrace":
        if not isinstance(raw, str):
            raise TraceError("trace json must be string")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise TraceError("invalid trace json") from exc
        if not isinstance(payload, dict):
            raise TraceError("trace payload must be object")
        try:
            identity = payload["identity"]
            proof = payload["proof"]
            sanity = payload["sanity"]
            action = payload["action"]
            fee = payload["fee"]
            chain = payload["chain"]
            state_proof = chain["state_proof"]
        except Exception as exc:
            raise TraceError("trace payload missing fields") from exc

        return cls(
            identity=IdentityTrace(commitment_hex=identity["commitment"]),
            proof=ProofEnvelopeTrace(
                protocol_version=proof["protocol_version"],
                statement_id=proof["statement_id"],
                context_id_hex=proof["context_id"],
                nonce_hex=proof["nonce"],
                public_inputs=proof["public_inputs"],
                proof_bytes_hex=proof["proof_bytes"],
                binding_tag_hex=proof["binding_tag"],
                nullifier_hex=proof.get("nullifier"),
            ),
            sanity=SanityTrace(
                wrong_context_verified=sanity["wrong_context_verified"],
                correct_context_verified=sanity["correct_context_verified"],
            ),
            action=ActionTrace(
                kind=action["kind"],
                module=action["module"],
                action=action["action"],
                payload=action["payload"],
                metadata=action["metadata"],
                action_hash_hex=action["action_hash"],
            ),
            fee=FeeTrace(
                payer=fee["payer"],
                components=fee["components"],
                total=fee["total"],
                quote_hash_hex=fee["quote_hash"],
                receipt_hash_hex=fee["receipt_hash"],
            ),
            chain=ChainTrace(
                chain_id=chain["chain_id"],
                sender=chain["sender"],
                nonce_hex=chain["nonce"],
                payload_hex=chain["payload"],
                signature_hex=chain["signature"],
                tx_hash_hex=chain["tx_hash"],
                block_height=chain["block_height"],
                block_hash_hex=chain["block_hash"],
                state_root_before_hex=chain["state_root_before"],
                state_root_after_hex=chain["state_root_after"],
                finality_proof_hex=chain["finality_proof"],
                state_proof=StateProofTrace(
                    key_hex=state_proof["key"],
                    value_hex=state_proof["value"],
                    state_root_hex=state_proof["state_root"],
                    proof_bytes_hex=state_proof["proof_bytes"],
                ),
            ),
        )
