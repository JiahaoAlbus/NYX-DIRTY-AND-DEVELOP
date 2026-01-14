import copy
import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "e2e-private-transfer" / "src"
PL_SRC = REPO_ROOT / "packages" / "l2-private-ledger" / "src"
ZK_SRC = REPO_ROOT / "packages" / "l0-zk-id" / "src"
ECON_SRC = REPO_ROOT / "packages" / "l2-economics" / "src"
CHAIN_SRC = REPO_ROOT / "packages" / "l1-chain" / "src"
KERNEL_SRC = REPO_ROOT / "packages" / "wallet-kernel" / "src"
for path in (SRC_DIR, PL_SRC, ZK_SRC, ECON_SRC, CHAIN_SRC, KERNEL_SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from e2e_private_transfer.pipeline import run_private_transfer  # noqa: E402
from e2e_private_transfer.replay import replay_and_verify  # noqa: E402
from e2e_private_transfer.trace import TransferTrace  # noqa: E402


def _flip_hex_byte(hex_value: str) -> str:
    data = bytearray(bytes.fromhex(hex_value))
    data[0] ^= 0x01
    return bytes(data).hex()


class TamperMatrixTests(unittest.TestCase):
    def test_tamper_matrix(self):
        trace, _ = run_private_transfer(seed=123)
        base = trace.to_dict()

        cases = []

        proof_bytes = copy.deepcopy(base)
        proof_bytes["proof"]["proof_bytes_hex"] = _flip_hex_byte(
            proof_bytes["proof"]["proof_bytes_hex"]
        )
        cases.append(proof_bytes)

        binding_tag = copy.deepcopy(base)
        binding_tag["proof"]["binding_tag_hex"] = _flip_hex_byte(
            binding_tag["proof"]["binding_tag_hex"]
        )
        cases.append(binding_tag)

        fee_vector = copy.deepcopy(base)
        components = fee_vector["fee"]["components"]
        components[0]["amount"] = int(components[0]["amount"]) + 1
        cases.append(fee_vector)

        receipt_hash = copy.deepcopy(base)
        receipt_hash["fee"]["receipt_hash_hex"] = _flip_hex_byte(
            receipt_hash["fee"]["receipt_hash_hex"]
        )
        cases.append(receipt_hash)

        payload = copy.deepcopy(base)
        payload["chain"]["payload_hex"] = _flip_hex_byte(payload["chain"]["payload_hex"])
        cases.append(payload)

        for index, payload_case in enumerate(cases):
            with self.subTest(index=index):
                tampered = TransferTrace.from_dict(payload_case)
                self.assertFalse(replay_and_verify(tampered))


if __name__ == "__main__":
    unittest.main()
