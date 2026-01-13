import json
import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
PATHS = [
    REPO_ROOT / "packages" / "l0-identity" / "src",
    REPO_ROOT / "packages" / "l0-zk-id" / "src",
    REPO_ROOT / "packages" / "l2-economics" / "src",
    REPO_ROOT / "packages" / "l1-chain" / "src",
    REPO_ROOT / "packages" / "wallet-kernel" / "src",
    REPO_ROOT / "packages" / "e2e-demo" / "src",
    REPO_ROOT / "packages" / "conformance-v1" / "src",
]
for path in PATHS:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from e2e_demo.pipeline import run_e2e  # noqa: E402
from e2e_demo.replay import replay_and_verify  # noqa: E402
from e2e_demo.trace import E2ETrace  # noqa: E402


def _tamper_hex(hex_str: str) -> str:
    last = hex_str[-1]
    replacement = "0" if last != "0" else "1"
    return hex_str[:-1] + replacement


class TamperDrillStricterTests(unittest.TestCase):
    def test_tamper_variants_fail_replay(self):
        trace, _ = run_e2e(seed=123)
        payload = json.loads(trace.to_json())

        mutators = [
            lambda data: data["proof"].__setitem__("proof_bytes", _tamper_hex(data["proof"]["proof_bytes"])),
            lambda data: data["action"].__setitem__("action_hash", _tamper_hex(data["action"]["action_hash"])),
            lambda data: data["fee"].__setitem__("quote_hash", _tamper_hex(data["fee"]["quote_hash"])),
            lambda data: data["chain"].__setitem__("tx_hash", _tamper_hex(data["chain"]["tx_hash"])),
            lambda data: data["chain"].__setitem__("state_root_after", _tamper_hex(data["chain"]["state_root_after"])),
        ]

        for mutate in mutators:
            mutated = json.loads(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
            mutate(mutated)
            tampered = E2ETrace.from_json(json.dumps(mutated, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
            replay = replay_and_verify(tampered)
            self.assertFalse(replay.ok)
            self.assertTrue(replay.errors)


if __name__ == "__main__":
    unittest.main()
