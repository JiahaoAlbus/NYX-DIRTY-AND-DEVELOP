from __future__ import annotations

import os
import re
import uuid
from dataclasses import dataclass
from typing import Literal, cast


class SettingsError(ValueError):
    pass


_ENV_CHOICES = {"dev", "staging", "prod"}
_RISK_MODE_CHOICES = {"off", "monitor", "enforce"}
_ADDRESS_MIN_LEN = 8
_SESSION_SECRET_MIN_LEN = 32
_KEY_MIN_LEN = 8
_UUID_RE = re.compile(r"^[a-fA-F0-9-]{36}$")


@dataclass(frozen=True)
class Settings:
    env: Literal["dev", "staging", "prod"]
    portal_session_secret: str
    portal_challenge_ttl: int
    portal_session_ttl: int
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
    compliance_enabled: bool
    compliance_url: str
    compliance_timeout_seconds: int
    compliance_fail_closed: bool
    risk_mode: Literal["off", "monitor", "enforce"]
    risk_global_mutations_paused: bool
    risk_global_max_per_min: int
    risk_global_max_amount_per_min: int
    risk_account_max_per_min: int
    risk_account_max_amount_per_min: int
    risk_ip_max_per_min: int
    risk_ip_max_amount_per_min: int
    risk_transfer_max_per_min: int
    risk_faucet_max_per_min: int
    risk_airdrop_max_per_min: int
    risk_exchange_orders_per_min: int
    risk_exchange_cancels_per_min: int
    risk_marketplace_orders_per_min: int
    risk_chat_messages_per_min: int
    risk_max_transfer_amount: int
    risk_max_faucet_amount: int
    risk_max_airdrop_amount: int
    risk_max_order_notional: int
    risk_max_store_notional: int
    risk_breaker_errors_per_min: int
    risk_breaker_window_seconds: int


def _require_env_choice(value: str) -> Literal["dev", "staging", "prod"]:
    normalized = value.strip().lower()
    if not normalized:
        return "dev"
    if normalized not in _ENV_CHOICES:
        raise SettingsError("NYX_ENV must be dev, staging, or prod")
    return cast(Literal["dev", "staging", "prod"], normalized)


def _require_risk_mode(value: str, env: str) -> Literal["off", "monitor", "enforce"]:
    normalized = value.strip().lower()
    if not normalized:
        if env == "dev":
            return "off"
        if env == "staging":
            return "monitor"
        return "enforce"
    if normalized not in _RISK_MODE_CHOICES:
        raise SettingsError("NYX_RISK_MODE must be off, monitor, or enforce")
    return cast(Literal["off", "monitor", "enforce"], normalized)


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


def _require_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    if raw in {"1", "true", "yes"}:
        return True
    if raw in {"0", "false", "no"}:
        return False
    raise SettingsError(f"{name} must be boolean")


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
    portal_session_ttl = _require_int(
        "NYX_PORTAL_SESSION_TTL",
        3600,
        min_value=300,
        max_value=24 * 60 * 60,
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

    compliance_enabled = _require_bool("NYX_COMPLIANCE_ENABLED", False)
    compliance_url = os.environ.get("NYX_COMPLIANCE_URL", "").strip()
    compliance_timeout_seconds = _require_int(
        "NYX_COMPLIANCE_TIMEOUT_SECONDS",
        3,
        min_value=1,
        max_value=60,
    )
    compliance_fail_closed = _require_bool("NYX_COMPLIANCE_FAIL_CLOSED", True)

    if compliance_enabled and env in {"staging", "prod"} and not compliance_url:
        raise SettingsError("NYX_COMPLIANCE_URL required when compliance is enabled")

    risk_mode = _require_risk_mode(os.environ.get("NYX_RISK_MODE", ""), env)
    risk_global_mutations_paused = _require_bool("NYX_RISK_GLOBAL_MUTATIONS_PAUSED", False)
    risk_global_max_per_min = _require_int(
        "NYX_RISK_GLOBAL_MAX_PER_MIN",
        600,
        min_value=0,
        max_value=100_000,
    )
    risk_global_max_amount_per_min = _require_int(
        "NYX_RISK_GLOBAL_MAX_AMOUNT_PER_MIN",
        10_000_000,
        min_value=0,
        max_value=1_000_000_000_000,
    )
    risk_account_max_per_min = _require_int(
        "NYX_RISK_ACCOUNT_MAX_PER_MIN",
        120,
        min_value=0,
        max_value=100_000,
    )
    risk_account_max_amount_per_min = _require_int(
        "NYX_RISK_ACCOUNT_MAX_AMOUNT_PER_MIN",
        2_000_000,
        min_value=0,
        max_value=1_000_000_000_000,
    )
    risk_ip_max_per_min = _require_int(
        "NYX_RISK_IP_MAX_PER_MIN",
        240,
        min_value=0,
        max_value=100_000,
    )
    risk_ip_max_amount_per_min = _require_int(
        "NYX_RISK_IP_MAX_AMOUNT_PER_MIN",
        3_000_000,
        min_value=0,
        max_value=1_000_000_000_000,
    )
    risk_transfer_max_per_min = _require_int(
        "NYX_RISK_TRANSFER_MAX_PER_MIN",
        30,
        min_value=0,
        max_value=100_000,
    )
    risk_faucet_max_per_min = _require_int(
        "NYX_RISK_FAUCET_MAX_PER_MIN",
        30,
        min_value=0,
        max_value=100_000,
    )
    risk_airdrop_max_per_min = _require_int(
        "NYX_RISK_AIRDROP_MAX_PER_MIN",
        30,
        min_value=0,
        max_value=100_000,
    )
    risk_exchange_orders_per_min = _require_int(
        "NYX_RISK_EXCHANGE_ORDERS_PER_MIN",
        60,
        min_value=0,
        max_value=100_000,
    )
    risk_exchange_cancels_per_min = _require_int(
        "NYX_RISK_EXCHANGE_CANCELS_PER_MIN",
        120,
        min_value=0,
        max_value=100_000,
    )
    risk_marketplace_orders_per_min = _require_int(
        "NYX_RISK_MARKETPLACE_ORDERS_PER_MIN",
        60,
        min_value=0,
        max_value=100_000,
    )
    risk_chat_messages_per_min = _require_int(
        "NYX_RISK_CHAT_MESSAGES_PER_MIN",
        120,
        min_value=0,
        max_value=100_000,
    )
    risk_max_transfer_amount = _require_int(
        "NYX_RISK_MAX_TRANSFER_AMOUNT",
        250_000,
        min_value=0,
        max_value=1_000_000_000_000,
    )
    risk_max_faucet_amount = _require_int(
        "NYX_RISK_MAX_FAUCET_AMOUNT",
        10_000,
        min_value=0,
        max_value=1_000_000_000_000,
    )
    risk_max_airdrop_amount = _require_int(
        "NYX_RISK_MAX_AIRDROP_AMOUNT",
        50_000,
        min_value=0,
        max_value=1_000_000_000_000,
    )
    risk_max_order_notional = _require_int(
        "NYX_RISK_MAX_ORDER_NOTIONAL",
        500_000,
        min_value=0,
        max_value=1_000_000_000_000,
    )
    risk_max_store_notional = _require_int(
        "NYX_RISK_MAX_STORE_NOTIONAL",
        250_000,
        min_value=0,
        max_value=1_000_000_000_000,
    )
    risk_breaker_errors_per_min = _require_int(
        "NYX_RISK_BREAKER_ERRORS_PER_MIN",
        40,
        min_value=0,
        max_value=100_000,
    )
    risk_breaker_window_seconds = _require_int(
        "NYX_RISK_BREAKER_WINDOW_SECONDS",
        60,
        min_value=10,
        max_value=3600,
    )

    return Settings(
        env=env,
        portal_session_secret=portal_session_secret,
        portal_challenge_ttl=portal_challenge_ttl,
        portal_session_ttl=portal_session_ttl,
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
        compliance_enabled=compliance_enabled,
        compliance_url=compliance_url,
        compliance_timeout_seconds=compliance_timeout_seconds,
        compliance_fail_closed=compliance_fail_closed,
        risk_mode=risk_mode,
        risk_global_mutations_paused=risk_global_mutations_paused,
        risk_global_max_per_min=risk_global_max_per_min,
        risk_global_max_amount_per_min=risk_global_max_amount_per_min,
        risk_account_max_per_min=risk_account_max_per_min,
        risk_account_max_amount_per_min=risk_account_max_amount_per_min,
        risk_ip_max_per_min=risk_ip_max_per_min,
        risk_ip_max_amount_per_min=risk_ip_max_amount_per_min,
        risk_transfer_max_per_min=risk_transfer_max_per_min,
        risk_faucet_max_per_min=risk_faucet_max_per_min,
        risk_airdrop_max_per_min=risk_airdrop_max_per_min,
        risk_exchange_orders_per_min=risk_exchange_orders_per_min,
        risk_exchange_cancels_per_min=risk_exchange_cancels_per_min,
        risk_marketplace_orders_per_min=risk_marketplace_orders_per_min,
        risk_chat_messages_per_min=risk_chat_messages_per_min,
        risk_max_transfer_amount=risk_max_transfer_amount,
        risk_max_faucet_amount=risk_max_faucet_amount,
        risk_max_airdrop_amount=risk_max_airdrop_amount,
        risk_max_order_notional=risk_max_order_notional,
        risk_max_store_notional=risk_max_store_notional,
        risk_breaker_errors_per_min=risk_breaker_errors_per_min,
        risk_breaker_window_seconds=risk_breaker_window_seconds,
    )
