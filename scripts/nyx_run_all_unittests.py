from __future__ import annotations

import sys
import os
import re
import subprocess
import tempfile
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _has_tests(path: Path) -> bool:
    return any(path.rglob("*_test.py"))


def _collect_test_dirs() -> list[Path]:
    repo_root = _repo_root()
    roots = [repo_root / "packages", repo_root / "apps", repo_root / "conformance"]
    explicit = [repo_root / "packages" / "l0-identity" / "test"]
    test_dirs: set[Path] = set()
    for path in explicit:
        if path.exists() and _has_tests(path):
            test_dirs.add(path.resolve())
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_dir():
                continue
            if "__pycache__" in path.parts:
                continue
            if path.name not in {"test", "tests"}:
                continue
            if _has_tests(path):
                test_dirs.add(path.resolve())
    return sorted(test_dirs)


def _create_l2_economics_shim() -> Path:
    shim_root = Path(tempfile.mkdtemp(prefix="nyx_test_shims_"))
    pkg_dir = shim_root / "l2_economics"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    init_content = "\n".join(
        [
            "from .action import *",
            "from .canonical import *",
            "from .engine import *",
            "from .fee import *",
            "from .hashing import *",
            "from .quote import *",
            "",
        ]
    )
    (pkg_dir / "__init__.py").write_text(init_content, encoding="utf-8")
    repo_root = _repo_root()
    src_root = repo_root / "packages" / "l2-economics" / "src"
    module_template = "\n".join(
        [
            "import sys as _sys",
            "from importlib import import_module as _import_module",
            "from pathlib import Path as _Path",
            "",
            f"_SRC = _Path({repr(str(src_root))})",
            "if str(_SRC) not in _sys.path:",
            "    _sys.path.insert(0, str(_SRC))",
            "",
            "_mod = _import_module(\"{module}\")",
            "_names = getattr(_mod, \"__all__\", None)",
            "if _names is None:",
            "    _names = [name for name in dir(_mod) if not name.startswith(\"_\")]",
            "for _name in _names:",
            "    globals()[_name] = getattr(_mod, _name)",
            "del _name, _names, _mod, _import_module, _Path, _SRC, _sys",
            "",
        ]
    )
    for module in ("action", "canonical", "engine", "fee", "hashing", "quote"):
        (pkg_dir / f"{module}.py").write_text(
            module_template.format(module=module), encoding="utf-8"
        )
    return shim_root


def _build_pythonpath(shim_root: Path | None) -> str:
    repo_root = _repo_root()
    paths: list[str] = []
    l2_src = repo_root / "packages" / "l2-economics" / "src"
    if l2_src.exists():
        paths.append(str(l2_src.resolve()))
    if shim_root is not None:
        paths.append(str(shim_root.resolve()))
    for base in (repo_root / "packages", repo_root / "apps"):
        if not base.exists():
            continue
        for src in base.rglob("src"):
            if src.is_dir():
                paths.append(str(src.resolve()))
    existing = os.environ.get("PYTHONPATH", "")
    if existing:
        paths.append(existing)
    return os.pathsep.join(paths)


def _run_discovery(test_dir: Path, shim_root: Path | None) -> tuple[int, int]:
    cmd = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        str(test_dir),
        "-p",
        "*_test.py",
        "-v",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = _build_pythonpath(shim_root)
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    output = (result.stdout or "") + (result.stderr or "")
    print(output, end="")
    matches = re.findall(r"Ran (\d+) tests", output)
    count = sum(int(value) for value in matches)
    return result.returncode, count


def _run_ios_fake_gate(repo_root: Path) -> int:
    gate = repo_root / "scripts" / "nyx_ios_no_fake_gate.py"
    if not gate.exists():
        return 0
    result = subprocess.run([sys.executable, str(gate)], capture_output=True, text=True)
    output = (result.stdout or "") + (result.stderr or "")
    print(output, end="")
    return result.returncode


def main() -> int:
    test_dirs = _collect_test_dirs()
    if not test_dirs:
        print("No test directories found.")
        return 1
    total_tests = 0
    shim_root = _create_l2_economics_shim()
    for test_dir in test_dirs:
        code, count = _run_discovery(test_dir, shim_root)
        total_tests += count
        if code != 0:
            return code
    gate_code = _run_ios_fake_gate(_repo_root())
    if gate_code != 0:
        return gate_code
    print(f"TOTAL_TESTS={total_tests}")
    if total_tests == 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
