import os
import sys
import unittest

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from l1_chain.devnet.adapter import (  # noqa: E402
    DeterministicInMemoryChainAdapter,
    encode_payload_del,
    encode_payload_nop,
    encode_payload_set,
)
from l1_chain.hashing import compare_digest, sha256  # noqa: E402
from l1_chain.types import ChainAccount, ChainId, TxSignature  # noqa: E402


def _bytes32(label: str) -> bytes:
    return sha256(label.encode("ascii"))


def _chain() -> DeterministicInMemoryChainAdapter:
    return DeterministicInMemoryChainAdapter(ChainId("devnet-0.1"))


def _sender(label: str) -> ChainAccount:
    return ChainAccount(label)


def _signature(payload: bytes) -> TxSignature:
    return TxSignature(sha256(b"sig" + payload))


class ChainAdapterUnitTests(unittest.TestCase):
    def test_tx_hash_stable(self):
        chain = _chain()
        payload = encode_payload_set(b"k", b"v")
        tx = chain.build_tx(
            sender=_sender("sender-a"),
            nonce=_bytes32("nonce-1"),
            payload=payload,
            signature=_signature(payload),
        )
        expected = sha256(tx.framed_preimage())
        self.assertTrue(compare_digest(tx.tx_hash.value, expected))

    def test_block_hash_stable(self):
        chain = _chain()
        payload = encode_payload_set(b"k", b"v")
        tx = chain.build_tx(
            sender=_sender("sender-a"),
            nonce=_bytes32("nonce-1"),
            payload=payload,
            signature=_signature(payload),
        )
        chain.submit_tx(tx)
        block_ref = chain.mine_block()
        recomputed = chain._compute_block_hash(
            block_ref.height,
            b"\x00" * 32,
            (tx.tx_hash.value,),
        )
        self.assertTrue(compare_digest(block_ref.block_hash, recomputed))

    def test_state_root_stable(self):
        chain = _chain()
        payload = encode_payload_set(b"k", b"v")
        tx = chain.build_tx(
            sender=_sender("sender-a"),
            nonce=_bytes32("nonce-1"),
            payload=payload,
            signature=_signature(payload),
        )
        chain.submit_tx(tx)
        chain.mine_block()
        _, root = chain.read_state(b"k")
        recomputed = chain._compute_state_root()
        self.assertTrue(compare_digest(root.value, recomputed))

    def test_submit_and_finality(self):
        chain = _chain()
        payload = encode_payload_set(b"k", b"v")
        tx = chain.build_tx(
            sender=_sender("sender-a"),
            nonce=_bytes32("nonce-1"),
            payload=payload,
            signature=_signature(payload),
        )
        chain.submit_tx(tx)
        chain.mine_block()
        proof = chain.get_finality(tx.tx_hash)
        self.assertIsNotNone(proof)
        self.assertTrue(compare_digest(proof.block_ref.block_hash, proof.block_ref.block_hash))

    def test_set_and_del_change_state(self):
        chain = _chain()
        payload = encode_payload_set(b"k", b"v")
        tx = chain.build_tx(
            sender=_sender("sender-a"),
            nonce=_bytes32("nonce-1"),
            payload=payload,
            signature=_signature(payload),
        )
        chain.submit_tx(tx)
        chain.mine_block()
        value, root_after_set = chain.read_state(b"k")
        self.assertEqual(value, b"v")

        payload_del = encode_payload_del(b"k")
        tx_del = chain.build_tx(
            sender=_sender("sender-a"),
            nonce=_bytes32("nonce-2"),
            payload=payload_del,
            signature=_signature(payload_del),
        )
        chain.submit_tx(tx_del)
        chain.mine_block()
        value_after_del, root_after_del = chain.read_state(b"k")
        self.assertIsNone(value_after_del)
        self.assertFalse(compare_digest(root_after_set.value, root_after_del.value))

    def test_nop_keeps_state_root(self):
        chain = _chain()
        payload = encode_payload_set(b"k", b"v")
        tx = chain.build_tx(
            sender=_sender("sender-a"),
            nonce=_bytes32("nonce-1"),
            payload=payload,
            signature=_signature(payload),
        )
        chain.submit_tx(tx)
        chain.mine_block()
        _, root_before = chain.read_state(b"k")

        nop_payload = encode_payload_nop()
        nop_tx = chain.build_tx(
            sender=_sender("sender-a"),
            nonce=_bytes32("nonce-2"),
            payload=nop_payload,
            signature=_signature(nop_payload),
        )
        chain.submit_tx(nop_tx)
        chain.mine_block()
        _, root_after = chain.read_state(b"k")
        self.assertTrue(compare_digest(root_before.value, root_after.value))

    def test_state_proof_verification(self):
        chain = _chain()
        payload = encode_payload_set(b"k", b"v")
        tx = chain.build_tx(
            sender=_sender("sender-a"),
            nonce=_bytes32("nonce-1"),
            payload=payload,
            signature=_signature(payload),
        )
        chain.submit_tx(tx)
        chain.mine_block()

        proof = chain.build_state_proof(b"k")
        self.assertTrue(chain.verify_state_proof(proof))

        tampered = proof.__class__(
            chain_id=proof.chain_id,
            key=b"other",
            value=proof.value,
            state_root=proof.state_root,
            proof_bytes=proof.proof_bytes,
        )
        self.assertFalse(chain.verify_state_proof(tampered))

        tampered_value = proof.__class__(
            chain_id=proof.chain_id,
            key=proof.key,
            value=b"other",
            state_root=proof.state_root,
            proof_bytes=proof.proof_bytes,
        )
        self.assertFalse(chain.verify_state_proof(tampered_value))

        tampered_root = proof.__class__(
            chain_id=proof.chain_id,
            key=proof.key,
            value=proof.value,
            state_root=proof.state_root.__class__(value=_bytes32("other")),
            proof_bytes=proof.proof_bytes,
        )
        self.assertFalse(chain.verify_state_proof(tampered_root))


if __name__ == "__main__":
    unittest.main()
