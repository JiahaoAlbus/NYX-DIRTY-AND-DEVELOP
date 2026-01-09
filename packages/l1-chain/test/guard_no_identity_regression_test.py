import inspect
import os
import sys
import unittest
from pathlib import Path

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import l1_chain.devnet.adapter as devnet_adapter  # noqa: E402
import l1_chain.types as types_module  # noqa: E402
from l1_chain.adapter import ChainAdapter  # noqa: E402
from l1_chain.devnet.adapter import (  # noqa: E402
    DeterministicInMemoryChainAdapter,
    encode_payload_set,
)
from l1_chain.hashing import sha256  # noqa: E402
from l1_chain.types import ChainAccount, ChainId, TxSignature  # noqa: E402

KEYWORDS = [
    "wallet",
    "identity",
    "account_as_identity",
    "address_as_identity",
    "privileged",
    "allowlist",
    "whitelist",
    "bypass",
    "override",
    "debug_free",
    "free_lane",
]

IMPORT_FORBIDDEN = [
    "l0_zk_id",
    "l0-zk-id",
    "l2_economics",
    "l2-economics",
]


def _sender(label: str) -> ChainAccount:
    return ChainAccount(label)


def _signature(payload: bytes) -> TxSignature:
    return TxSignature(sha256(b"sig" + payload))


class ChainGuardTests(unittest.TestCase):
    def test_no_keywords_in_src(self):
        src_root = Path(__file__).resolve().parents[1] / "src"
        for root, _, files in os.walk(src_root):
            for filename in files:
                if not filename.endswith(".py"):
                    continue
                content = Path(root, filename).read_text(encoding="utf-8", errors="ignore").lower()
                for keyword in KEYWORDS:
                    self.assertNotIn(keyword, content, msg=f"{keyword} found in {filename}")

    def test_no_forbidden_imports(self):
        src_root = Path(__file__).resolve().parents[1] / "src"
        for root, _, files in os.walk(src_root):
            for filename in files:
                if not filename.endswith(".py"):
                    continue
                content = Path(root, filename).read_text(encoding="utf-8", errors="ignore")
                for token in IMPORT_FORBIDDEN:
                    self.assertNotIn(token, content, msg=f"{token} import found in {filename}")

    def test_chain_adapter_api_guard(self):
        banned = [
            "identity",
            "wallet",
        ]
        for method in ("submit_tx", "get_finality", "read_state", "verify_state_proof"):
            signature = inspect.signature(getattr(ChainAdapter, method))
            for param in signature.parameters.values():
                name = param.name.lower()
                for token in banned:
                    self.assertNotIn(token, name)

    def test_compare_digest_usage_in_tx(self):
        chain_id = ChainId("devnet-0.1")
        payload = encode_payload_set(b"k", b"v")
        tx = DeterministicInMemoryChainAdapter(chain_id).build_tx(
            sender=_sender("sender-a"),
            nonce=sha256(b"nonce"),
            payload=payload,
            signature=_signature(payload),
        )
        calls = {"count": 0}
        original = types_module.compare_digest

        def wrapped(left, right):
            calls["count"] += 1
            return original(left, right)

        types_module.compare_digest = wrapped
        try:
            _ = types_module.TxEnvelope(
                chain_id=tx.chain_id,
                sender=tx.sender,
                nonce=tx.nonce,
                payload=tx.payload,
                signature=tx.signature,
                tx_hash=tx.tx_hash,
            )
        finally:
            types_module.compare_digest = original
        self.assertGreater(calls["count"], 0)

    def test_compare_digest_usage_in_state_proof(self):
        chain = DeterministicInMemoryChainAdapter(ChainId("devnet-0.1"))
        payload = encode_payload_set(b"k", b"v")
        tx = chain.build_tx(
            sender=_sender("sender-a"),
            nonce=sha256(b"nonce"),
            payload=payload,
            signature=_signature(payload),
        )
        chain.submit_tx(tx)
        chain.mine_block()
        proof = chain.build_state_proof(b"k")

        calls = {"count": 0}
        original = devnet_adapter.compare_digest

        def wrapped(left, right):
            calls["count"] += 1
            return original(left, right)

        devnet_adapter.compare_digest = wrapped
        try:
            self.assertTrue(chain.verify_state_proof(proof))
        finally:
            devnet_adapter.compare_digest = original
        self.assertGreater(calls["count"], 0)


if __name__ == "__main__":
    unittest.main()
