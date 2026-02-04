from __future__ import annotations

import re
import sys
from pathlib import Path

BANNED = re.compile(r"\b(todo|mock|placeholder|example)\b", re.IGNORECASE)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _should_skip(path: Path) -> bool:
    lowered = {part.lower() for part in path.parts}
    if "node_modules" in lowered or "dist" in lowered or "build" in lowered:
        return True
    if "test" in lowered or "tests" in lowered:
        return True
    return False


def main() -> int:
    repo_root = _repo_root()
    web_root = repo_root / "nyx-world"
    if not web_root.exists():
        print("OK: no nyx-world sources found")
        return 0

    offenders: list[str] = []
    for path in web_root.rglob("*"):
        if path.is_dir():
            continue
        if path.suffix not in {".ts", ".tsx", ".js", ".jsx"}:
            continue
        if _should_skip(path):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for idx, line in enumerate(text.splitlines(), start=1):
            # Allow HTML/JSX placeholder attributes (they are UX affordances, not fake UI).
            # Still ban "placeholder" in other contexts (e.g. "placeholder data", "placeholder button").
            scan_line = re.sub(r"\bplaceholder\s*=", "ph=", line)
            if BANNED.search(scan_line):
                offenders.append(f"{path}:{idx}: {line.strip()}")

    if offenders:
        print("FAIL: banned tokens in web runtime sources")
        for item in offenders:
            print(item)
        return 1

    print("OK: no fake tokens in web runtime")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
