#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: generate_manifest.py <release_dir> [output_path]", file=sys.stderr)
        return 2
    release_dir = Path(sys.argv[1]).resolve()
    if not release_dir.is_dir():
        print(f"release dir not found: {release_dir}", file=sys.stderr)
        return 2
    output_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else release_dir / "manifest.json"

    skip = {"SHA256SUMS.txt", output_path.name}
    entries: list[dict[str, object]] = []
    for path in sorted(release_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(release_dir).as_posix()
        if path.name in skip:
            continue
        entries.append(
            {
                "path": rel,
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "release_dir": str(release_dir),
        "artifacts": entries,
    }
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
