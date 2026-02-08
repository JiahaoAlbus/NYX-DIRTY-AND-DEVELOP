#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ALLOWLIST = {
    "PUBLIC_KEYS_AND_REPLACEMENTS.md",
    ".env.example",
    "NYX-DIRTY-AND-DEVELOP/.env.example",
}

PATTERNS = {
    "NYX_0X_API_KEY": re.compile(r"NYX_0X_API_KEY\s*=\s*([A-Fa-f0-9-]{16,})"),
    "NYX_JUPITER_API_KEY": re.compile(r"NYX_JUPITER_API_KEY\s*=\s*([A-Fa-f0-9-]{16,})"),
    "NYX_MAGIC_EDEN_API_KEY": re.compile(r"NYX_MAGIC_EDEN_API_KEY\s*=\s*(\S{8,})"),
    "NYX_PAYEVM_API_KEY": re.compile(r"NYX_PAYEVM_API_KEY\s*=\s*(\S{8,})"),
    "AWS_ACCESS_KEY_ID": re.compile(r"AKIA[0-9A-Z]{16}"),
    "STRIPE_LIVE_KEY": re.compile(r"sk_live_[0-9a-zA-Z]{16,}"),
}


def _is_text(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            chunk = handle.read(2048)
        return b"\x00" not in chunk
    except Exception:
        return False


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    findings: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel.startswith((".git/", "node_modules/", "release_artifacts/", "docs/evidence/", "nyx-world/dist/")):
            continue
        if rel in ALLOWLIST:
            continue
        if not _is_text(path):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for label, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                findings.append(f"{label} in {rel}: {match.group(0)[:80]}")

    if findings:
        print("Secret scan failed. Potential secrets detected:")
        for item in findings:
            print(f"- {item}")
        return 2

    print("Secret scan OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
