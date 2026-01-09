from __future__ import annotations

from l1_chain.devnet.adapter import (
    DeterministicInMemoryChainAdapter,
    encode_payload_nop,
    encode_payload_set,
)
from l1_chain.hashing import compare_digest, sha256
from l1_chain.types import ChainAccount, ChainId, TxSignature


def _bytes32(label: str) -> bytes:
    return sha256(label.encode("ascii"))


def main() -> None:
    chain = DeterministicInMemoryChainAdapter(ChainId("devnet-0.1"))
    sender = ChainAccount("devnet-sender")

    key = b"alpha"
    value = b"one"
    payload = encode_payload_set(key, value)
    signature = TxSignature(sha256(b"sig" + payload))
    tx = chain.build_tx(
        sender=sender,
        nonce=_bytes32("nonce-1"),
        payload=payload,
        signature=signature,
    )
    chain.submit_tx(tx)
    block_ref = chain.mine_block()
    state_value, state_root = chain.read_state(key)

    print("devnet-set-tx-hash:", tx.tx_hash.value.hex())
    print("devnet-set-block-height:", block_ref.height)
    print("devnet-set-block-hash:", block_ref.block_hash.hex())
    print("devnet-set-state-root:", state_root.value.hex())
    print("devnet-set-value:", state_value.hex() if state_value is not None else "<none>")

    nop_payload = encode_payload_nop()
    nop_signature = TxSignature(sha256(b"sig" + nop_payload))
    nop_tx = chain.build_tx(
        sender=sender,
        nonce=_bytes32("nonce-2"),
        payload=nop_payload,
        signature=nop_signature,
    )
    chain.submit_tx(nop_tx)
    nop_block_ref = chain.mine_block()
    _, nop_state_root = chain.read_state(key)

    print("devnet-nop-tx-hash:", nop_tx.tx_hash.value.hex())
    print("devnet-nop-block-height:", nop_block_ref.height)
    print("devnet-nop-block-hash:", nop_block_ref.block_hash.hex())
    print("devnet-nop-state-root:", nop_state_root.value.hex())
    print("devnet-nop-state-root-unchanged:", compare_digest(state_root.value, nop_state_root.value))


if __name__ == "__main__":
    main()
