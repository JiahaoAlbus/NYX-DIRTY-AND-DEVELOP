from __future__ import annotations

import os
from pathlib import Path

from nyx_backend_gateway.storage import StorageError


def load_env_file(path: Path) -> None:
    if not path.exists():
        raise StorageError("env file not found")
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key:
            os.environ.setdefault(key, value)


def get_fee_address() -> str:
    address = os.environ.get("NYX_TESTNET_FEE_ADDRESS", "").strip()
    if not address:
        raise StorageError("NYX_TESTNET_FEE_ADDRESS required")
    if len(address) < 8:
        raise StorageError("NYX_TESTNET_FEE_ADDRESS too short")
    return address
