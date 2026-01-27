#!/usr/bin/env python3
import re
import sys
from pathlib import Path

RUNTIME_DIRS = [
    Path("apps/nyx-backend-gateway/src/nyx_backend_gateway"),
    Path("apps/nyx-backend/src/nyx_backend"),
    Path("apps/nyx-ios"),
]

PATTERNS = [
    re.compile(r"\bTODO\b"),
    re.compile(r"\bFIXME\b"),
    re.compile(r"\bplaceholder\b", re.IGNORECASE),
    re.compile(r"\bexample\b", re.IGNORECASE),
    re.compile(r"\bfake\b", re.IGNORECASE),
    re.compile(r"mock response", re.IGNORECASE),
]


def main() -> int:
    violations = []
    for root in RUNTIME_DIRS:
        if not root.exists():
            continue
        for path in list(root.rglob("*.py")) + list(root.rglob("*.swift")):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in PATTERNS:
                for match in pattern.finditer(text):
                    line_no = text.count("\n", 0, match.start()) + 1
                    violations.append(f"{path}:{line_no}: {pattern.pattern}")
    if violations:
        sys.stderr.write("Runtime fake/placeholder tokens detected:\n")
        sys.stderr.write("\n".join(violations) + "\n")
        return 1
    print("No fake/placeholder tokens detected in runtime code.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
