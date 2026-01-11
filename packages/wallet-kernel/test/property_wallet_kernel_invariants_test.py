import os
import random
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

from wallet_kernel.canonical import (
    CanonicalizationError,
    compare_digest,
    require_bytes32,
    sha256,
)  # noqa: E402
from wallet_kernel.keystore import InMemoryKeyStore  # noqa: E402
from wallet_kernel.kernel import WalletKernel  # noqa: E402
from wallet_kernel.secrets import SecretBytes  # noqa: E402
from wallet_kernel.signing import HMACSigner  # noqa: E402
from wallet_kernel.tx_plumbing import NonceSource, TxBuilder  # noqa: E402

RNG = random.Random(610)
PROPERTY_N = 2000


class FixedNonceSource(NonceSource):
    def __init__(self, nonce: bytes) -> None:
        self._nonce = nonce

    def next_nonce(self) -> bytes:
        return self._nonce


def _kernel_with_nonce(nonce: bytes) -> WalletKernel:
    keystore = InMemoryKeyStore()
    secret = SecretBytes(b"property-secret")
    keystore.put_key("key-1", secret)
    return WalletKernel(
        chain_id=ChainId("devnet-0.1"),
        keystore=keystore,
        signer=HMACSigner(),
        nonce_source=FixedNonceSource(nonce),
        proof_adapter=MockProofAdapter(),
    )


class WalletKernelPropertyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        print(f"PROPERTY_N={PROPERTY_N}")

    def test_signing_invariants(self):
        for index in range(PROPERTY_N):
            payload = RNG.randbytes(12)
            nonce = sha256(f"nonce-{index}".encode("ascii"))
            kernel = _kernel_with_nonce(nonce)
            sender = ChainAccount(f"sender-{index}")
            request = kernel.build_action(sender=sender, payload=payload)
            signed = kernel.sign_action(request, "key-1")
            secret = kernel.keystore.get_key("key-1")
            self.assertTrue(
                kernel.signer.verify(
                    payload,
                    signed.tx_envelope.signature.value,
                    secret,
                )
            )
            expected = TxBuilder(
                keystore=kernel.keystore,
                signer=kernel.signer,
                nonce_source=FixedNonceSource(nonce),
            ).build_and_sign_tx(
                chain_id=kernel.chain_id,
                sender=sender,
                key_id="key-1",
                payload=payload,
            )
            self.assertTrue(
                compare_digest(signed.tx_envelope.tx_hash.value, expected.tx_hash.value)
            )

    def test_sender_variation(self):
        for index in range(PROPERTY_N):
            payload = RNG.randbytes(10)
            nonce = sha256(f"nonce-sender-{index}".encode("ascii"))
            kernel_a = _kernel_with_nonce(nonce)
            kernel_b = _kernel_with_nonce(nonce)
            sender_a = ChainAccount("sender-a")
            sender_b = ChainAccount("sender-b")
            request_a = kernel_a.build_action(sender=sender_a, payload=payload)
            request_b = kernel_b.build_action(sender=sender_b, payload=payload)
            signed_a = kernel_a.sign_action(request_a, "key-1")
            signed_b = kernel_b.sign_action(request_b, "key-1")
            self.assertFalse(
                compare_digest(
                    signed_a.tx_envelope.tx_hash.value,
                    signed_b.tx_envelope.tx_hash.value,
                )
            )

    def test_proof_context_invariants(self):
        statement_id = "personhood.v0"
        for index in range(PROPERTY_N):
            context_id = sha256(f"context-{index}".encode("ascii"))
            envelope = prove_mock(
                statement_id=statement_id,
                context_id=context_id,
                nonce=sha256(f"nonce-proof-{index}".encode("ascii")),
                public_inputs={"claim": True, "level": index % 3},
                witness={"secret": f"value-{index}"},
            )
            kernel = _kernel_with_nonce(sha256(b"nonce-fixed"))
            self.assertTrue(
                kernel.verify_proofs([envelope], context_id, statement_id)
            )
            wrong_context = sha256(f"context-{index}-wrong".encode("ascii"))
            self.assertFalse(
                kernel.verify_proofs([envelope], wrong_context, statement_id)
            )

    def test_bytes32_validation(self):
        for index in range(PROPERTY_N):
            length = RNG.randint(0, 64)
            if length == 32:
                continue
            with self.assertRaises(CanonicalizationError):
                require_bytes32(b"x" * length, "value")


if __name__ == "__main__":
    unittest.main()
