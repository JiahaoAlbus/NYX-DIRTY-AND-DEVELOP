import re
import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "conformance-v1" / "src" / "conformance_v1"
if str(REPO_ROOT / "packages" / "conformance-v1" / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "packages" / "conformance-v1" / "src"))


def _join(parts: list[str]) -> str:
    return "".join(parts)


_WAL = "wal"
_LET = "let"
_ID_A = "iden"
_ID_B = "tity"
_PR_A = "priv"
_PR_B = "ileged"
_BY_A = "by"
_BY_B = "pass"

_W_WORD = _join([_WAL, _LET])
_ID_WORD = _join([_ID_A, _ID_B])
_PR_WORD = _join([_PR_A, _PR_B])
_BY_WORD = _join([_BY_A, _BY_B])

_PATTERN_W_ID = re.compile(
    _W_WORD
    + ".*"
    + _ID_WORD,
    re.IGNORECASE,
)
_PATTERN_P_B = re.compile(
    _PR_WORD
    + ".*"
    + _BY_WORD,
    re.IGNORECASE,
)


class FrozenGateSequenceGuardTests(unittest.TestCase):
    def test_no_frozen_gate_sequences(self):
        for path in SRC_DIR.rglob("*.py"):
            content = path.read_text(encoding="utf-8", errors="ignore")
            for line_no, line in enumerate(content.splitlines(), start=1):
                self.assertIsNone(
                    _PATTERN_W_ID.search(line),
                    msg=f"sequence hit at {path}:{line_no}",
                )
                self.assertIsNone(
                    _PATTERN_P_B.search(line),
                    msg=f"sequence hit at {path}:{line_no}",
                )


if __name__ == "__main__":
    unittest.main()
