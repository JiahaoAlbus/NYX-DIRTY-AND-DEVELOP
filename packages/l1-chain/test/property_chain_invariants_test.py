import os
import random
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

RNG = random.Random(505)
PROPERTY_N = 2000


def _bytes32(label: str) -> bytes:
    return sha256(label.encode("ascii"))


def _chain() -> DeterministicInMemoryChainAdapter:
    return DeterministicInMemoryChainAdapter(ChainId("devnet-0.1"))


def _sender(label: str) -> ChainAccount:
    return ChainAccount(label)


def _signature(payload: bytes) -> TxSignature:
    return TxSignature(sha256(b"sig" + payload))


def _random_key() -> bytes:
    return RNG.randbytes(4)


def _random_value() -> bytes:
    return RNG.randbytes(6)


class ChainPropertyTests(unittest.TestCase):
    def test_payload_semantics(self):
        chain = _chain()
        model: dict[bytes, bytes] = {}
        for index in range(PROPERTY_N):
            op_choice = RNG.random()
            if op_choice < 0.5:
                key = _random_key()
                value = _random_value()
                payload = encode_payload_set(key, value)
                expected_change = model.get(key) != value
                model[key] = value
            elif op_choice < 0.8:
                key = _random_key()
                payload = encode_payload_del(key)
                expected_change = key in model
                if key in model:
                    del model[key]
            else:
                payload = encode_payload_nop()
                expected_change = False

            prev_root = chain.read_state(b"")[1].value
            tx = chain.build_tx(
                sender=_sender(f"sender-{index}"),
                nonce=_bytes32(f"nonce-{index}"),
                payload=payload,
                signature=_signature(payload),
            )
            chain.submit_tx(tx)
            chain.mine_block()
            new_root = chain.read_state(b"")[1].value
            if expected_change:
                self.assertFalse(compare_digest(prev_root, new_root))
            else:
                self.assertTrue(compare_digest(prev_root, new_root))

    def test_sender_independence(self):
        for index in range(PROPERTY_N):
            key = _random_key()
            value = _random_value()
            payload = encode_payload_set(key, value)

            chain_a = _chain()
            chain_b = _chain()

            tx_a = chain_a.build_tx(
                sender=_sender("sender-a"),
                nonce=_bytes32(f"nonce-a-{index}"),
                payload=payload,
                signature=_signature(payload),
            )
            tx_b = chain_b.build_tx(
                sender=_sender("sender-b"),
                nonce=_bytes32(f"nonce-b-{index}"),
                payload=payload,
                signature=_signature(payload),
            )
            chain_a.submit_tx(tx_a)
            chain_b.submit_tx(tx_b)
            chain_a.mine_block()
            chain_b.mine_block()

            value_a, root_a = chain_a.read_state(key)
            value_b, root_b = chain_b.read_state(key)
            self.assertEqual(value_a, value_b)
            self.assertTrue(compare_digest(root_a.value, root_b.value))
            self.assertFalse(compare_digest(tx_a.tx_hash.value, tx_b.tx_hash.value))


if __name__ == "__main__":
    unittest.main()
