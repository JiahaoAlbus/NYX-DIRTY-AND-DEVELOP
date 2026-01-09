from __future__ import annotations

from dataclasses import dataclass

from l1_chain.canonical import CanonicalizationError, canonicalize, require_text
from l1_chain.hashing import (
    HASH_BYTES,
    HashingError,
    bytes32_hex,
    compare_digest,
    encode_len_prefixed,
    encode_len_prefixed_bytes,
    require_bytes32,
    sha256,
)


class TypeErrorL1(ValueError):
    pass


@dataclass(frozen=True)
class ChainId:
    value: str

    def __post_init__(self) -> None:
        try:
            require_text(self.value, "chain_id")
        except CanonicalizationError as exc:
            raise TypeErrorL1(str(exc)) from exc


@dataclass(frozen=True)
class ChainAccount:
    value: str

    def __post_init__(self) -> None:
        try:
            require_text(self.value, "sender")
        except CanonicalizationError as exc:
            raise TypeErrorL1(str(exc)) from exc


@dataclass(frozen=True)
class TxSignature:
    value: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.value, bytes):
            raise TypeErrorL1("signature must be bytes")
        if len(self.value) == 0:
            raise TypeErrorL1("signature must be non-empty")


@dataclass(frozen=True)
class TxHash:
    value: bytes

    def __post_init__(self) -> None:
        try:
            require_bytes32(self.value, "tx_hash")
        except HashingError as exc:
            raise TypeErrorL1(str(exc)) from exc


@dataclass(frozen=True)
class StateRoot:
    value: bytes

    def __post_init__(self) -> None:
        try:
            require_bytes32(self.value, "state_root")
        except HashingError as exc:
            raise TypeErrorL1(str(exc)) from exc


@dataclass(frozen=True)
class BlockRef:
    height: int
    block_hash: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.height, int) or isinstance(self.height, bool):
            raise TypeErrorL1("height must be int")
        if self.height < 0:
            raise TypeErrorL1("height must be >= 0")
        try:
            require_bytes32(self.block_hash, "block_hash")
        except HashingError as exc:
            raise TypeErrorL1(str(exc)) from exc

    def canonical_bytes(self) -> bytes:
        payload = {
            "height": self.height,
            "block_hash": bytes32_hex(self.block_hash, "block_hash"),
        }
        try:
            return canonicalize(payload)
        except CanonicalizationError as exc:
            raise TypeErrorL1(str(exc)) from exc

    def sha256(self) -> bytes:
        return sha256(self.canonical_bytes())


@dataclass(frozen=True)
class TxEnvelope:
    chain_id: ChainId
    sender: ChainAccount
    nonce: bytes
    payload: bytes
    signature: TxSignature
    tx_hash: TxHash

    def __post_init__(self) -> None:
        if not isinstance(self.chain_id, ChainId):
            raise TypeErrorL1("chain_id must be ChainId")
        if not isinstance(self.sender, ChainAccount):
            raise TypeErrorL1("sender must be ChainAccount")
        if not isinstance(self.signature, TxSignature):
            raise TypeErrorL1("signature must be TxSignature")
        if not isinstance(self.tx_hash, TxHash):
            raise TypeErrorL1("tx_hash must be TxHash")
        if not isinstance(self.nonce, bytes):
            raise TypeErrorL1("nonce must be bytes")
        if len(self.nonce) != HASH_BYTES:
            raise TypeErrorL1("nonce must be 32 bytes")
        if not isinstance(self.payload, bytes):
            raise TypeErrorL1("payload must be bytes")

        expected = self._compute_hash_value()
        if not compare_digest(self.tx_hash.value, expected):
            raise TypeErrorL1("tx_hash mismatch")

    def canonical_bytes(self) -> bytes:
        payload = {
            "chain_id": self.chain_id.value,
            "sender": self.sender.value,
            "nonce": self.nonce.hex(),
            "payload": self.payload.hex(),
            "signature": self.signature.value.hex(),
            "tx_hash": self.tx_hash.value.hex(),
        }
        try:
            return canonicalize(payload)
        except CanonicalizationError as exc:
            raise TypeErrorL1(str(exc)) from exc

    def framed_preimage(self) -> bytes:
        return b"".join(
            [
                encode_len_prefixed(self.chain_id.value, "chain_id"),
                encode_len_prefixed(self.sender.value, "sender"),
                encode_len_prefixed_bytes(self.nonce, "nonce"),
                encode_len_prefixed_bytes(self.payload, "payload"),
                encode_len_prefixed_bytes(self.signature.value, "signature"),
            ]
        )

    def _compute_hash_value(self) -> bytes:
        return sha256(self.framed_preimage())


@dataclass(frozen=True)
class FinalityProof:
    chain_id: ChainId
    block_ref: BlockRef
    proof_bytes: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.chain_id, ChainId):
            raise TypeErrorL1("chain_id must be ChainId")
        if not isinstance(self.block_ref, BlockRef):
            raise TypeErrorL1("block_ref must be BlockRef")
        if not isinstance(self.proof_bytes, bytes):
            raise TypeErrorL1("proof_bytes must be bytes")

    def canonical_bytes(self) -> bytes:
        payload = {
            "chain_id": self.chain_id.value,
            "block_ref": {
                "height": self.block_ref.height,
                "block_hash": bytes32_hex(self.block_ref.block_hash, "block_hash"),
            },
            "proof_bytes": self.proof_bytes.hex(),
        }
        try:
            return canonicalize(payload)
        except CanonicalizationError as exc:
            raise TypeErrorL1(str(exc)) from exc

    def sha256(self) -> bytes:
        return sha256(self.canonical_bytes())


@dataclass(frozen=True)
class StateProof:
    chain_id: ChainId
    key: bytes
    value: bytes | None
    state_root: StateRoot
    proof_bytes: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.chain_id, ChainId):
            raise TypeErrorL1("chain_id must be ChainId")
        if not isinstance(self.state_root, StateRoot):
            raise TypeErrorL1("state_root must be StateRoot")
        if not isinstance(self.key, bytes):
            raise TypeErrorL1("key must be bytes")
        if self.value is not None and not isinstance(self.value, bytes):
            raise TypeErrorL1("value must be bytes or None")
        if not isinstance(self.proof_bytes, bytes):
            raise TypeErrorL1("proof_bytes must be bytes")

    def canonical_bytes(self) -> bytes:
        payload = {
            "chain_id": self.chain_id.value,
            "key": self.key.hex(),
            "value": None if self.value is None else self.value.hex(),
            "state_root": bytes32_hex(self.state_root.value, "state_root"),
            "proof_bytes": self.proof_bytes.hex(),
        }
        try:
            return canonicalize(payload)
        except CanonicalizationError as exc:
            raise TypeErrorL1(str(exc)) from exc

    def sha256(self) -> bytes:
        return sha256(self.canonical_bytes())


def build_tx_envelope(
    *,
    chain_id: ChainId,
    sender: ChainAccount,
    nonce: bytes,
    payload: bytes,
    signature: TxSignature,
) -> TxEnvelope:
    preimage = TxEnvelope(
        chain_id=chain_id,
        sender=sender,
        nonce=nonce,
        payload=payload,
        signature=signature,
        tx_hash=TxHash(value=sha256(
            b"".join(
                [
                    encode_len_prefixed(chain_id.value, "chain_id"),
                    encode_len_prefixed(sender.value, "sender"),
                    encode_len_prefixed_bytes(nonce, "nonce"),
                    encode_len_prefixed_bytes(payload, "payload"),
                    encode_len_prefixed_bytes(signature.value, "signature"),
                ]
            )
        )),
    )
    return preimage
