import os
import re
from pathlib import Path
import unittest


class GuardNoSenderSemanticsTests(unittest.TestCase):
    def test_no_sender_like_tokens(self):
        repo_root = Path(__file__).resolve().parents[3]
        src_dir = repo_root / "packages" / "l2-private-ledger" / "src"
        patterns = [r"\bsender\b", r"\baccount\b", r"\baddress\b"]
        regexes = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        for root, _, files in os.walk(src_dir):
            for file_name in files:
                if not file_name.endswith(".py"):
                    continue
                path = Path(root) / file_name
                content = path.read_text(encoding="utf-8")
                for regex in regexes:
                    self.assertIsNone(regex.search(content), msg=str(path))


if __name__ == "__main__":
    unittest.main()
