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


def get_treasury_address() -> str:
    address = os.environ.get("NYX_TESTNET_TREASURY_ADDRESS", "").strip()
    if not address:
        address = os.environ.get("NYX_TESTNET_FEE_ADDRESS", "").strip()
    if not address:
        return "testnet-treasury-unconfigured"
    if len(address) < 8:
        raise StorageError("NYX_TESTNET_TREASURY_ADDRESS too short")
    return address


def get_fee_address() -> str:
    return get_treasury_address()


def get_platform_fee_bps() -> int | None:
    raw = os.environ.get("NYX_PLATFORM_FEE_BPS", "").strip()
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError as exc:
        raise StorageError("NYX_PLATFORM_FEE_BPS must be int") from exc
    if value < 0 or value > 10_000:
        raise StorageError("NYX_PLATFORM_FEE_BPS out of bounds")
    return value


def get_protocol_fee_min() -> int | None:
    raw = os.environ.get("NYX_PROTOCOL_FEE_MIN", "").strip()
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError as exc:
        raise StorageError("NYX_PROTOCOL_FEE_MIN must be int") from exc
    if value < 0:
        raise StorageError("NYX_PROTOCOL_FEE_MIN out of bounds")
    return value
