from __future__ import annotations

import os
from pathlib import Path

from nyx_backend_gateway.settings import SettingsError, get_settings
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


def _settings():
    try:
        return get_settings()
    except SettingsError as exc:
        raise StorageError(str(exc)) from exc


def get_treasury_address() -> str:
    return _settings().treasury_address


def get_fee_address() -> str:
    return get_treasury_address()


def get_platform_fee_bps() -> int:
    return _settings().platform_fee_bps


def get_protocol_fee_min() -> int | None:
    return _settings().protocol_fee_min


def get_portal_session_secret() -> str:
    return _settings().portal_session_secret


def get_portal_challenge_ttl_seconds() -> int:
    return _settings().portal_challenge_ttl


def get_faucet_cooldown_seconds() -> int:
    return _settings().faucet_cooldown_seconds


def get_faucet_max_amount_per_24h() -> int:
    return _settings().faucet_max_amount_per_24h


def get_faucet_max_claims_per_24h() -> int:
    return _settings().faucet_max_claims_per_24h


def get_faucet_ip_max_claims_per_24h() -> int:
    return _settings().faucet_ip_max_claims_per_24h


def get_0x_api_key() -> str:
    return _settings().api_0x_key


def get_jupiter_api_key() -> str:
    return _settings().api_jupiter_key


def get_magic_eden_api_key() -> str:
    return _settings().api_magic_eden_key


def get_payevm_api_key() -> str:
    return _settings().api_payevm_key
