import inspect
import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PATHS = [
    REPO_ROOT / "packages" / "wallet-kernel" / "src",
    REPO_ROOT / "packages" / "l1-chain" / "src",
    REPO_ROOT / "packages" / "l0-zk-id" / "src",
]
for path in PATHS:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from l1_chain.types import ChainAccount, ChainId  # noqa: E402
from prover.mock import prove_mock  # noqa: E402
from verifier import MockProofAdapter  # noqa: E402

from wallet_kernel.canonical import compare_digest, sha256  # noqa: E402
from wallet_kernel.errors import PolicyError, ValidationError  # noqa: E402
from wallet_kernel.keystore import InMemoryKeyStore  # noqa: E402
from wallet_kernel.kernel import WalletKernel  # noqa: E402
from wallet_kernel.policy import Capability  # noqa: E402
from wallet_kernel.proof_plumbing import ProofVerifier  # noqa: E402
from wallet_kernel.secrets import SecretBytes  # noqa: E402
from wallet_kernel.signing import HMACSigner  # noqa: E402
from wallet_kernel.tx_plumbing import NonceSource, TxBuilder  # noqa: E402


class FixedNonceSource(NonceSource):
    def __init__(self, nonce: bytes) -> None:
        self._nonce = nonce

    def next_nonce(self) -> bytes:
        return self._nonce


class WalletKernelUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.chain_id = ChainId("devnet-0.1")
        self.keystore = InMemoryKeyStore()
        self.secret = SecretBytes(b"unit-secret")
        self.keystore.put_key("key-1", self.secret)
        self.signer = HMACSigner()
        self.nonce = sha256(b"nonce-1")
        self.adapter = MockProofAdapter()
        self.kernel = WalletKernel(
            chain_id=self.chain_id,
            keystore=self.keystore,
            signer=self.signer,
            nonce_source=FixedNonceSource(self.nonce),
            proof_adapter=self.adapter,
        )

    def test_secret_repr_redacted(self):
        secret = SecretBytes(b"very-secret")
        rendered = repr(secret) + str(secret)
        self.assertNotIn("very-secret", rendered)
        self.assertNotIn(b"very-secret".hex(), rendered)

    def test_keystore_roundtrip(self):
        key_id = "alpha"
        secret = SecretBytes(b"alpha-secret")
        store = InMemoryKeyStore()
        store.put_key(key_id, secret)
        self.assertIs(store.get_key(key_id), secret)
        self.assertEqual(store.list_keys(), [key_id])
        store.delete_key(key_id)
        self.assertEqual(store.list_keys(), [])

    def test_signer_sign_verify(self):
        message = b"payload"
        signature = self.signer.sign(message, self.secret)
        self.assertTrue(self.signer.verify(message, signature, self.secret))
        self.assertFalse(self.signer.verify(message + b"x", signature, self.secret))

    def test_tx_builder_stable_hash(self):
        payload = b"payload"
        sender = ChainAccount("sender-1")
        builder = TxBuilder(
            keystore=self.keystore,
            signer=self.signer,
            nonce_source=FixedNonceSource(self.nonce),
        )
        tx_a = builder.build_and_sign_tx(
            chain_id=self.chain_id,
            sender=sender,
            key_id="key-1",
            payload=payload,
        )
        tx_b = builder.build_and_sign_tx(
            chain_id=self.chain_id,
            sender=sender,
            key_id="key-1",
            payload=payload,
        )
        self.assertTrue(compare_digest(tx_a.tx_hash.value, tx_b.tx_hash.value))

    def test_tx_builder_rejects_bad_nonce(self):
        class BadNonce(NonceSource):
            def next_nonce(self) -> bytes:
                return b"short"

        builder = TxBuilder(
            keystore=self.keystore,
            signer=self.signer,
            nonce_source=BadNonce(),
        )
        with self.assertRaises(ValidationError):
            builder.build_and_sign_tx(
                chain_id=self.chain_id,
                sender=ChainAccount("sender-1"),
                key_id="key-1",
                payload=b"payload",
            )

    def test_proof_verifier_no_prove(self):
        self.assertFalse(hasattr(ProofVerifier, "prove"))

    def test_kernel_api_names(self):
        banned = ("identity", "root")
        for name, member in inspect.getmembers(WalletKernel, predicate=callable):
            if name.startswith("_"):
                continue
            lowered = name.lower()
            for token in banned:
                self.assertNotIn(token, lowered)
            self.assertTrue(callable(member))

    def test_policy_default_deny(self):
        sender = ChainAccount("sender-1")
        request = self.kernel.build_action(
            sender=sender,
            payload=b"payload",
            requires_capability=True,
            capability=Capability("cap-1"),
        )
        with self.assertRaises(PolicyError):
            self.kernel.sign_action(request, "key-1")

    def test_proof_verification(self):
        envelope = prove_mock(
            statement_id="personhood.v0",
            context_id=sha256(b"context-1"),
            nonce=sha256(b"nonce-1"),
            public_inputs={"claim": True},
            witness={"secret": "value"},
        )
        self.assertTrue(
            self.kernel.verify_proofs(
                [envelope],
                expected_context_id=sha256(b"context-1"),
                expected_statement_id="personhood.v0",
            )
        )
        self.assertFalse(
            self.kernel.verify_proofs(
                [envelope],
                expected_context_id=sha256(b"context-2"),
                expected_statement_id="personhood.v0",
            )
        )


if __name__ == "__main__":
    unittest.main()
