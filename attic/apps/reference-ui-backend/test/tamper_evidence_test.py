import json
import tempfile
from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
PATHS = [
    REPO_ROOT / "apps" / "reference-ui-backend" / "src",
    REPO_ROOT / "packages" / "e2e-private-transfer" / "src",
    REPO_ROOT / "packages" / "l2-private-ledger" / "src",
    REPO_ROOT / "packages" / "l0-zk-id" / "src",
    REPO_ROOT / "packages" / "l2-economics" / "src",
    REPO_ROOT / "packages" / "l1-chain" / "src",
    REPO_ROOT / "packages" / "wallet-kernel" / "src",
]
for path in PATHS:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from nyx_reference_ui_backend import evidence as ev  # noqa: E402
from nyx_reference_ui_backend.evidence import (  # noqa: E402
    EvidenceError,
    load_evidence,
    run_evidence,
    verify_evidence_payload,
)


class TamperEvidenceTests(unittest.TestCase):
    def test_tamper_outputs_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            run_id = "tamper-1"
            run_evidence(seed=123, run_id=run_id, base_dir=base_dir)
            run_dir = base_dir / ev._run_key(run_id)
            outputs_path = run_dir / "artifacts" / "outputs.json"
            payload = json.loads(outputs_path.read_text(encoding="utf-8"))
            payload["state_hash"] = "00" + payload["state_hash"][2:]
            outputs_path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")), encoding="utf-8")
            evidence = load_evidence(run_id, base_dir)
            with self.assertRaises(EvidenceError):
                verify_evidence_payload(evidence)

    def test_tamper_receipt_hashes_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            run_id = "tamper-2"
            run_evidence(seed=123, run_id=run_id, base_dir=base_dir)
            run_dir = base_dir / ev._run_key(run_id)
            receipt_path = run_dir / "artifacts" / "receipt_hashes.json"
            hashes = json.loads(receipt_path.read_text(encoding="utf-8"))
            hashes[0] = "00" + hashes[0][2:]
            receipt_path.write_text(json.dumps(hashes, sort_keys=True, separators=(",", ":")), encoding="utf-8")
            evidence = load_evidence(run_id, base_dir)
            with self.assertRaises(EvidenceError):
                verify_evidence_payload(evidence)


if __name__ == "__main__":
    unittest.main()
