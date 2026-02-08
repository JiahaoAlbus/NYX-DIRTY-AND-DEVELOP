from __future__ import annotations

import os
import re
import uuid
from dataclasses import dataclass
from typing import Literal, cast


class SettingsError(ValueError):
    pass


_ENV_CHOICES = {"dev", "staging", "prod"}
_ADDRESS_MIN_LEN = 8
_SESSION_SECRET_MIN_LEN = 32
_KEY_MIN_LEN = 8
_UUID_RE = re.compile(r"^[a-fA-F0-9-]{36}$")


@dataclass(frozen=True)
class Settings:
    env: Literal["dev", "staging", "prod"]
    portal_session_secret: str
    portal_challenge_ttl: int
    treasury_address: str
    platform_fee_bps: int
    protocol_fee_min: int | None
    faucet_cooldown_seconds: int
    faucet_max_amount_per_24h: int
    faucet_max_claims_per_24h: int
    faucet_ip_max_claims_per_24h: int
    api_0x_key: str
    api_jupiter_key: str
    api_magic_eden_key: str
    api_payevm_key: str


def _require_env_choice(value: str) -> Literal["dev", "staging", "prod"]:
    normalized = value.strip().lower()
    if not normalized:
        return "dev"
    if normalized not in _ENV_CHOICES:
        raise SettingsError("NYX_ENV must be dev, staging, or prod")
    return cast(Literal["dev", "staging", "prod"], normalized)


def _require_int(name: str, default: int, *, min_value: int, max_value: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise SettingsError(f"{name} must be int") from exc
    if value < min_value or value > max_value:
        raise SettingsError(f"{name} out of bounds")
    return value


def _optional_int(name: str, *, min_value: int, max_value: int) -> int | None:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError as exc:
        raise SettingsError(f"{name} must be int") from exc
    if value < min_value or value > max_value:
        raise SettingsError(f"{name} out of bounds")
    return value


def _require_secret(env: str) -> str:
    secret = os.environ.get("NYX_PORTAL_SESSION_SECRET", "").strip()
    if not secret:
        if env == "dev":
            return "testnet-session-secret"
        raise SettingsError("NYX_PORTAL_SESSION_SECRET required for staging/prod")
    if env in {"staging", "prod"} and len(secret) < _SESSION_SECRET_MIN_LEN:
        raise SettingsError("NYX_PORTAL_SESSION_SECRET too short for staging/prod")
    return secret


def _require_treasury_address(env: str) -> str:
    address = os.environ.get("NYX_TESTNET_TREASURY_ADDRESS", "").strip()
    if not address:
        address = os.environ.get("NYX_TESTNET_FEE_ADDRESS", "").strip()
    if not address:
        if env == "dev":
            return "0x0Aa313fCE773786C8425a13B96DB64205c5edCBc"
        raise SettingsError("NYX_TESTNET_TREASURY_ADDRESS required for staging/prod")
    if len(address) < _ADDRESS_MIN_LEN:
        raise SettingsError("NYX_TESTNET_TREASURY_ADDRESS too short")
    return address


def _validate_uuid_key(name: str, value: str) -> str:
    if not value:
        return ""
    if not _UUID_RE.fullmatch(value):
        raise SettingsError(f"{name} must be UUID format")
    try:
        uuid.UUID(value)
    except ValueError as exc:
        raise SettingsError(f"{name} must be UUID format") from exc
    return value


def _validate_generic_key(name: str, value: str) -> str:
    if not value:
        return ""
    if len(value) < _KEY_MIN_LEN:
        raise SettingsError(f"{name} too short")
    if any(ch.isspace() for ch in value):
        raise SettingsError(f"{name} invalid")
    return value


def get_settings() -> Settings:
    env = _require_env_choice(os.environ.get("NYX_ENV", "dev"))
    portal_session_secret = _require_secret(env)
    portal_challenge_ttl = _require_int(
        "NYX_PORTAL_CHALLENGE_TTL",
        300,
        min_value=60,
        max_value=3600,
    )
    treasury_address = _require_treasury_address(env)
    platform_fee_bps = _require_int(
        "NYX_PLATFORM_FEE_BPS",
        10,
        min_value=0,
        max_value=10_000,
    )
    protocol_fee_min = _optional_int(
        "NYX_PROTOCOL_FEE_MIN",
        min_value=0,
        max_value=1_000_000_000,
    )
    faucet_cooldown_seconds = _require_int(
        "NYX_FAUCET_COOLDOWN_SECONDS",
        24 * 60 * 60,
        min_value=0,
        max_value=30 * 24 * 60 * 60,
    )
    faucet_max_amount_per_24h = _require_int(
        "NYX_FAUCET_MAX_AMOUNT_PER_24H",
        1_000,
        min_value=0,
        max_value=1_000_000_000,
    )
    faucet_max_claims_per_24h = _require_int(
        "NYX_FAUCET_MAX_CLAIMS_PER_24H",
        1,
        min_value=0,
        max_value=1000,
    )
    faucet_ip_max_claims_per_24h = _require_int(
        "NYX_FAUCET_IP_MAX_CLAIMS_PER_24H",
        5,
        min_value=0,
        max_value=10_000,
    )

    api_0x_key = _validate_uuid_key("NYX_0X_API_KEY", os.environ.get("NYX_0X_API_KEY", "").strip())
    api_jupiter_key = _validate_uuid_key("NYX_JUPITER_API_KEY", os.environ.get("NYX_JUPITER_API_KEY", "").strip())
    api_magic_eden_key = _validate_generic_key(
        "NYX_MAGIC_EDEN_API_KEY", os.environ.get("NYX_MAGIC_EDEN_API_KEY", "").strip()
    )
    api_payevm_key = _validate_generic_key("NYX_PAYEVM_API_KEY", os.environ.get("NYX_PAYEVM_API_KEY", "").strip())

    return Settings(
        env=env,
        portal_session_secret=portal_session_secret,
        portal_challenge_ttl=portal_challenge_ttl,
        treasury_address=treasury_address,
        platform_fee_bps=platform_fee_bps,
        protocol_fee_min=protocol_fee_min,
        faucet_cooldown_seconds=faucet_cooldown_seconds,
        faucet_max_amount_per_24h=faucet_max_amount_per_24h,
        faucet_max_claims_per_24h=faucet_max_claims_per_24h,
        faucet_ip_max_claims_per_24h=faucet_ip_max_claims_per_24h,
        api_0x_key=api_0x_key,
        api_jupiter_key=api_jupiter_key,
        api_magic_eden_key=api_magic_eden_key,
        api_payevm_key=api_payevm_key,
    )
