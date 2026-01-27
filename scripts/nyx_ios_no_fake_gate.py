from __future__ import annotations

import re
import sys
from pathlib import Path


BANNED = re.compile(r"\b(todo|mock|placeholder|example)\b", re.IGNORECASE)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    repo_root = _repo_root()
    ios_root = repo_root / "apps" / "nyx-ios"
    if not ios_root.exists():
        print("OK: no iOS sources found")
        return 0

    offenders: list[str] = []
    for path in ios_root.rglob("*.swift"):
        if "Tests" in path.parts or "tests" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for idx, line in enumerate(text.splitlines(), start=1):
            if BANNED.search(line):
                offenders.append(f"{path}:{idx}: {line.strip()}")

    if offenders:
        print("FAIL: banned tokens in iOS runtime sources")
        for item in offenders:
            print(item)
        return 1

    print("OK: no fake tokens in iOS runtime")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
