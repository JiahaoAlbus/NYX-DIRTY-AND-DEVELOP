import ast
import inspect
import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PATHS = [
    REPO_ROOT / "packages" / "wallet-kernel" / "src",
    REPO_ROOT / "packages" / "l1-chain" / "src",
    REPO_ROOT / "packages" / "l0-zk-id" / "src",
]
for path in PATHS:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from wallet_kernel.kernel import WalletKernel  # noqa: E402
from wallet_kernel.secrets import SecretBytes  # noqa: E402
from wallet_kernel.keystore import InMemoryKeyStore  # noqa: E402

KEYWORDS = [
    "root secret",
    "root_secret",
    "seed",
    "mnemonic",
    "export",
    "upload",
    "exfiltrate",
    "export_raw",
    "identity root",
    "address_as_identity",
    "account_as_identity",
    "allowlist",
    "whitelist",
    "bypass",
    "override",
    "debug_free",
    "free_lane",
]

FORBIDDEN_IMPORTS = [
    "l0_identity",
    "l0-identity",
    "packages.l0_identity",
]

PROVE_CALLS = {
    "prove",
    "prove_mock",
}


def _scan_python_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith(".py"):
                files.append(Path(path) / filename)
    return files


class WalletKernelGuardTests(unittest.TestCase):
    def test_no_keywords_in_src(self):
        src_root = REPO_ROOT / "packages" / "wallet-kernel" / "src"
        for file_path in _scan_python_files(src_root):
            content = file_path.read_text(encoding="utf-8", errors="ignore").lower()
            for keyword in KEYWORDS:
                self.assertNotIn(keyword, content, msg=f"{keyword} found in {file_path}")

    def test_no_forbidden_imports(self):
        src_root = REPO_ROOT / "packages" / "wallet-kernel" / "src"
        for file_path in _scan_python_files(src_root):
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            for token in FORBIDDEN_IMPORTS:
                self.assertNotIn(token, content, msg=f"{token} found in {file_path}")

    def test_verify_only_calls(self):
        src_root = REPO_ROOT / "packages" / "wallet-kernel" / "src"
        for file_path in _scan_python_files(src_root):
            tree = ast.parse(file_path.read_text(encoding="utf-8", errors="ignore"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                if isinstance(func, ast.Name):
                    self.assertNotIn(func.id, PROVE_CALLS, msg=f"{func.id} used in {file_path}")
                if isinstance(func, ast.Attribute):
                    self.assertNotIn(func.attr, PROVE_CALLS, msg=f"{func.attr} used in {file_path}")

    def test_api_guard(self):
        banned = ("identity", "root")
        for name, member in inspect.getmembers(WalletKernel, predicate=callable):
            if name.startswith("_"):
                continue
            lowered = name.lower()
            for token in banned:
                self.assertNotIn(token, lowered)
            signature = inspect.signature(member)
            for param in signature.parameters.values():
                lowered_param = param.name.lower()
                for token in banned:
                    self.assertNotIn(token, lowered_param)

    def test_secret_not_leaked(self):
        secret_bytes = b"guard-secret"
        secret = SecretBytes(secret_bytes)
        store = InMemoryKeyStore()
        store.put_key("guard-key", secret)
        outputs = [repr(secret), str(secret), repr(store), str(store)]
        combined = "".join(outputs)
        self.assertNotIn(secret_bytes.decode("ascii"), combined)
        self.assertNotIn(secret_bytes.hex(), combined)


if __name__ == "__main__":
    unittest.main()
