import subprocess
import sys
import unittest
from pathlib import Path


class NoFakeTokensGateTest(unittest.TestCase):
    def test_ios_and_web_no_fake_tokens(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        scripts = [
            repo_root / "scripts" / "nyx_ios_no_fake_gate.py",
            repo_root / "scripts" / "no_fake_gate_web.py",
        ]
        for script in scripts:
            result = subprocess.run(
                [sys.executable, str(script)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                self.fail(
                    f"{script.name} failed:\n{result.stdout}\n{result.stderr}"
                )
