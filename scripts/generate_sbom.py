#!/usr/bin/env python3
from __future__ import annotations

import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path


def _add_component(components: list[dict], *, name: str, version: str, scope: str, ctype: str = "library") -> None:
    components.append(
        {
            "type": ctype,
            "name": name,
            "version": version,
            "scope": scope,
        }
    )


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "release_artifacts" / "sbom.json"

    components: list[dict] = []

    pkg_path = root / "nyx-world" / "package.json"
    if pkg_path.exists():
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
        _add_component(
            components,
            name=str(pkg.get("name", "nyx-world")),
            version=str(pkg.get("version", "0.0.0")),
            scope="application",
            ctype="application",
        )
        deps = pkg.get("dependencies") or {}
        for name in sorted(deps.keys()):
            _add_component(components, name=name, version=str(deps[name]), scope="runtime")
        dev_deps = pkg.get("devDependencies") or {}
        for name in sorted(dev_deps.keys()):
            _add_component(components, name=name, version=str(dev_deps[name]), scope="development")

    _add_component(
        components,
        name="python",
        version=platform.python_version(),
        scope="runtime",
        ctype="runtime",
    )

    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.4",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "tools": [{"vendor": "nyx", "name": "generate_sbom.py", "version": "1.0"}],
        },
        "components": components,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(sbom, indent=2, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
