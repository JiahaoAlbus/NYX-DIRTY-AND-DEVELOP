import re
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

RUNTIME_DIRS = [
    Path(__file__).resolve().parents[2] / "src" / "nyx_backend_gateway",
    Path(__file__).resolve().parents[3] / "nyx-backend" / "src" / "nyx_backend",
]

PATTERNS = [
    re.compile(r"\bTODO\b"),
    re.compile(r"\bFIXME\b"),
    re.compile(r"\bplaceholder\b", re.IGNORECASE),
    re.compile(r"\bexample\b", re.IGNORECASE),
    re.compile(r"\bfake\b", re.IGNORECASE),
    re.compile(r"mock response", re.IGNORECASE),
]


class NoFakeCodeCheckTests(unittest.TestCase):
    def test_runtime_has_no_fake_tokens(self) -> None:
        violations = []
        for root in RUNTIME_DIRS:
            if not root.exists():
                continue
            for path in root.rglob("*.py"):
                text = path.read_text(encoding="utf-8", errors="ignore")
                for pattern in PATTERNS:
                    if pattern.search(text):
                        violations.append(f"{path}:{pattern.pattern}")
        self.assertFalse(violations, "\n".join(violations))


if __name__ == "__main__":
    unittest.main()
