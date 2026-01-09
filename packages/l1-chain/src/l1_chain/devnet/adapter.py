from __future__ import annotations

from dataclasses import dataclass

from l1_chain.adapter import ChainAdapter
from l1_chain.canonical import CanonicalizationError, canonicalize
from l1_chain.hashing import (
    HASH_BYTES,
    HashingError,
    compare_digest,
    require_bytes32,
    sha256,
)
from l1_chain.types import (
    BlockRef,
    ChainAccount,
    ChainId,
    FinalityProof,
    StateProof,
    StateRoot,
    TxEnvelope,
    TxHash,
    TxSignature,
    build_tx_envelope,
)

OP_SET = 0x01
OP_DEL = 0x02
OP_NOP = 0x10


class DevnetError(ValueError):
    pass


@dataclass(frozen=True)
class _Block:
    height: int
    block_hash: bytes
    prev_hash: bytes
    tx_hashes: tuple[bytes, ...]
    state_root: bytes

    def block_ref(self) -> BlockRef:
        return BlockRef(height=self.height, block_hash=self.block_hash)


class DeterministicInMemoryChainAdapter(ChainAdapter):
    def __init__(self, chain_id: ChainId) -> None:
        if not isinstance(chain_id, ChainId):
            raise DevnetError("chain_id must be ChainId")
        self._chain_id = chain_id
        self._state: dict[bytes, bytes] = {}
        self._mempool: list[TxEnvelope] = []
        self._blocks: list[_Block] = []
        self._tx_index: list[tuple[bytes, BlockRef]] = []
        self._state_root = self._compute_state_root()

    @property
    def chain_id(self) -> ChainId:
        return self._chain_id

    def submit_tx(self, tx: TxEnvelope) -> TxHash:
        if not isinstance(tx, TxEnvelope):
            raise DevnetError("tx must be TxEnvelope")
        if tx.chain_id.value != self._chain_id.value:
            raise DevnetError("chain_id mismatch")
        expected = tx._compute_hash_value()
        if not compare_digest(tx.tx_hash.value, expected):
            raise DevnetError("tx_hash mismatch")
        if not self._verify_signature(tx):
            raise DevnetError("signature invalid")
        self._mempool.append(tx)
        return tx.tx_hash

    def get_finality(self, tx_hash: TxHash) -> FinalityProof | None:
        if not isinstance(tx_hash, TxHash):
            raise DevnetError("tx_hash must be TxHash")
        for entry_hash, block_ref in self._tx_index:
            if compare_digest(entry_hash, tx_hash.value):
                return self._build_finality(block_ref)
        return None

    def read_state(self, key: bytes) -> tuple[bytes | None, StateRoot]:
        if not isinstance(key, bytes):
            raise DevnetError("key must be bytes")
        value = self._state.get(key)
        return value, StateRoot(value=self._state_root)

    def verify_state_proof(self, proof: StateProof) -> bool:
        if not isinstance(proof, StateProof):
            return False
        if proof.chain_id.value != self._chain_id.value:
            return False
        expected_bytes = self._state_proof_bytes(
            proof.chain_id,
            proof.key,
            proof.value,
            proof.state_root,
        )
        if not compare_digest(proof.proof_bytes, expected_bytes):
            return False
        if not compare_digest(proof.state_root.value, self._state_root):
            return False
        return True

    def mine_block(self) -> BlockRef:
        height = len(self._blocks)
        prev_hash = self._blocks[-1].block_hash if self._blocks else b"\x00" * HASH_BYTES
        txs = tuple(self._mempool)
        self._mempool = []
        tx_hashes = tuple(tx.tx_hash.value for tx in txs)
        for tx in txs:
            self._apply_payload(tx.payload)
        self._state_root = self._compute_state_root()
        block_hash = self._compute_block_hash(height, prev_hash, tx_hashes)
        block = _Block(
            height=height,
            block_hash=block_hash,
            prev_hash=prev_hash,
            tx_hashes=tx_hashes,
            state_root=self._state_root,
        )
        self._blocks.append(block)
        block_ref = block.block_ref()
        for tx_hash in tx_hashes:
            self._tx_index.append((tx_hash, block_ref))
        return block_ref

    def build_state_proof(self, key: bytes) -> StateProof:
        value = self._state.get(key)
        state_root = StateRoot(value=self._state_root)
        proof_bytes = self._state_proof_bytes(self._chain_id, key, value, state_root)
        return StateProof(
            chain_id=self._chain_id,
            key=key,
            value=value,
            state_root=state_root,
            proof_bytes=proof_bytes,
        )

    def build_tx(
        self,
        *,
        sender: ChainAccount,
        nonce: bytes,
        payload: bytes,
        signature: TxSignature,
    ) -> TxEnvelope:
        return build_tx_envelope(
            chain_id=self._chain_id,
            sender=sender,
            nonce=nonce,
            payload=payload,
            signature=signature,
        )

    def _verify_signature(self, tx: TxEnvelope) -> bool:
        if not isinstance(tx.signature.value, bytes):
            return False
        return len(tx.signature.value) > 0

    def _apply_payload(self, payload: bytes) -> None:
        op, key, value = decode_payload(payload)
        if op == OP_NOP:
            return
        if op == OP_SET:
            if value is None:
                raise DevnetError("SET requires value")
            self._state[key] = value
            return
        if op == OP_DEL:
            if key in self._state:
                del self._state[key]
            return
        raise DevnetError("unsupported op")

    def _compute_state_root(self) -> bytes:
        items = [
            {"k": key.hex(), "v": value.hex()}
            for key, value in sorted(self._state.items(), key=lambda pair: pair[0])
        ]
        try:
            return sha256(canonicalize(items))
        except CanonicalizationError as exc:
            raise DevnetError(str(exc)) from exc

    def _compute_block_hash(
        self, height: int, prev_hash: bytes, tx_hashes: tuple[bytes, ...]
    ) -> bytes:
        if not isinstance(height, int) or isinstance(height, bool):
            raise DevnetError("height must be int")
        if height < 0:
            raise DevnetError("height must be >= 0")
        try:
            require_bytes32(prev_hash, "prev_hash")
        except HashingError as exc:
            raise DevnetError(str(exc)) from exc
        merkle_root = compute_merkle_root(tx_hashes)
        height_bytes = height.to_bytes(8, "big")
        return sha256(height_bytes + prev_hash + merkle_root)

    def _build_finality(self, block_ref: BlockRef) -> FinalityProof:
        proof_bytes = sha256(block_ref.canonical_bytes())
        return FinalityProof(
            chain_id=self._chain_id,
            block_ref=block_ref,
            proof_bytes=proof_bytes,
        )

    def _state_proof_bytes(
        self,
        chain_id: ChainId,
        key: bytes,
        value: bytes | None,
        state_root: StateRoot,
    ) -> bytes:
        payload = {
            "chain_id": chain_id.value,
            "key": key.hex(),
            "value": None if value is None else value.hex(),
            "state_root": state_root.value.hex(),
        }
        try:
            return sha256(canonicalize(payload))
        except CanonicalizationError as exc:
            raise DevnetError(str(exc)) from exc


def encode_payload_set(key: bytes, value: bytes) -> bytes:
    return _encode_payload(OP_SET, key, value)


def encode_payload_del(key: bytes) -> bytes:
    return _encode_payload(OP_DEL, key, b"")


def encode_payload_nop() -> bytes:
    return bytes([OP_NOP]) + (0).to_bytes(4, "big") + (0).to_bytes(4, "big")


def decode_payload(payload: bytes) -> tuple[int, bytes, bytes | None]:
    if not isinstance(payload, bytes):
        raise DevnetError("payload must be bytes")
    if len(payload) < 1 + 4 + 4:
        raise DevnetError("payload too short")
    op = payload[0]
    key_len = int.from_bytes(payload[1:5], "big")
    cursor = 5
    if len(payload) < cursor + key_len + 4:
        raise DevnetError("payload truncated")
    key = payload[cursor : cursor + key_len]
    cursor += key_len
    val_len = int.from_bytes(payload[cursor : cursor + 4], "big")
    cursor += 4
    if len(payload) != cursor + val_len:
        raise DevnetError("payload length mismatch")
    value = payload[cursor : cursor + val_len] if val_len > 0 else b""
    if op == OP_NOP:
        if key_len != 0 or val_len != 0:
            raise DevnetError("NOP must have empty key/value")
        return op, b"", None
    if op == OP_SET:
        if key_len == 0:
            raise DevnetError("SET requires key")
        if val_len == 0:
            raise DevnetError("SET requires value")
        return op, key, value
    if op == OP_DEL:
        if key_len == 0:
            raise DevnetError("DEL requires key")
        if val_len != 0:
            raise DevnetError("DEL must have empty value")
        return op, key, None
    raise DevnetError("unsupported op")


def _encode_payload(op: int, key: bytes, value: bytes) -> bytes:
    if not isinstance(key, bytes):
        raise DevnetError("key must be bytes")
    if not isinstance(value, bytes):
        raise DevnetError("value must be bytes")
    return bytes([op]) + len(key).to_bytes(4, "big") + key + len(value).to_bytes(4, "big") + value


def compute_merkle_root(tx_hashes: tuple[bytes, ...]) -> bytes:
    if not tx_hashes:
        return sha256(b"")
    level = list(tx_hashes)
    for entry in level:
        require_bytes32(entry, "tx_hash")
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        next_level: list[bytes] = []
        for index in range(0, len(level), 2):
            next_level.append(sha256(level[index] + level[index + 1]))
        level = next_level
    return level[0]
