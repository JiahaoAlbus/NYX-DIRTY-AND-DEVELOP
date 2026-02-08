from __future__ import annotations

import json
import re
from typing import Any

from nyx_backend_gateway.assets import is_supported_asset
from nyx_backend_gateway.errors import GatewayApiError, GatewayError

_MAX_AMOUNT = 1_000_000
_MAX_PRICE = 1_000_000
_ENTERTAINMENT_MODES = {"pulse", "drift", "scan"}
_ADDRESS_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def require_text(payload: dict[str, Any], key: str, max_len: int = 64) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value or isinstance(value, bool):
        raise GatewayApiError("PARAM_REQUIRED", f"{key} required", http_status=400, details={"param": key})
    value = value.strip()
    if len(value) > max_len:
        raise GatewayApiError("PARAM_INVALID", f"{key} too long", http_status=400, details={"param": key})
    if not _ADDRESS_PATTERN.fullmatch(value):
        raise GatewayApiError("PARAM_INVALID", f"{key} invalid", http_status=400, details={"param": key})
    return value


def require_address(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    return validate_address_text(value, key)


def validate_address_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value or isinstance(value, bool):
        raise GatewayError(f"{name} required")
    text = value.strip()
    if not _ADDRESS_PATTERN.fullmatch(text):
        raise GatewayError(f"{name} invalid")
    return text


def require_amount(payload: dict[str, Any], key: str = "amount", max_value: int = _MAX_AMOUNT) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise GatewayError(f"{key} must be int")
    if value <= 0 or value > max_value:
        raise GatewayError(f"{key} out of bounds")
    return value


def validate_wallet_transfer(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise GatewayError("payload must be object")
    result = dict(payload)
    result["from_address"] = require_address(payload, "from_address")
    result["to_address"] = require_address(payload, "to_address")
    result["amount"] = require_amount(payload, "amount")
    result["asset_id"] = require_asset_id(payload, "asset_id")
    return result


def validate_wallet_faucet(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise GatewayError("payload must be object")
    result = dict(payload)
    result["address"] = require_address(payload, "address")
    result["amount"] = require_amount(payload, "amount")
    result["asset_id"] = require_asset_id(payload, "asset_id")
    return result


def require_token(payload: dict[str, Any], key: str = "token") -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value or isinstance(value, bool):
        raise GatewayError(f"{key} required")
    if len(value) > 512:
        raise GatewayError(f"{key} too long")
    return value


def require_asset_id(payload: dict[str, Any], key: str = "asset_id") -> str:
    value = payload.get(key, "NYXT")
    if not isinstance(value, str) or not value or isinstance(value, bool):
        raise GatewayError(f"{key} required")
    asset_id = value.strip()
    if not is_supported_asset(asset_id):
        raise GatewayError(f"{key} unsupported")
    return asset_id


def require_int(payload: dict[str, Any], key: str, min_value: int = 1, max_value: int | None = None) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise GatewayError(f"{key} must be int")
    if value < min_value:
        raise GatewayError(f"{key} out of bounds")
    if max_value is not None and value > max_value:
        raise GatewayError(f"{key} out of bounds")
    return value


def validate_exchange_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise GatewayError("payload must be object")
    required = ("side", "amount", "price", "asset_in", "asset_out", "owner_address")
    for key in required:
        if key not in payload:
            raise GatewayError(f"{key} required")
    result = dict(payload)
    result["side"] = str(payload["side"]).upper()
    if result["side"] not in {"BUY", "SELL"}:
        raise GatewayError("side invalid")
    result["amount"] = require_int(payload, "amount", min_value=1, max_value=_MAX_AMOUNT)
    result["price"] = require_int(payload, "price", min_value=1, max_value=_MAX_PRICE)
    result["asset_in"] = require_asset_id(payload, "asset_in")
    result["asset_out"] = require_asset_id(payload, "asset_out")
    result["owner_address"] = validate_address_text(payload["owner_address"], "owner_address")
    return result


def validate_place_order(payload: dict[str, Any]) -> dict[str, Any]:
    return validate_exchange_payload(payload)


def validate_cancel(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise GatewayError("payload must be object")
    order_id = payload.get("order_id")
    if not isinstance(order_id, str) or not order_id:
        raise GatewayError("order_id required")
    return {"order_id": order_id.strip()}


def validate_chat_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise GatewayError("payload must be object")
    channel = payload.get("channel")
    message = payload.get("message")
    if not isinstance(channel, str) or not channel:
        raise GatewayError("channel required")
    if not isinstance(message, str) or not message:
        raise GatewayError("message required")
    if len(channel) > 64:
        raise GatewayError("channel too long")
    if len(message) > 2000:
        raise GatewayError("message too long")
    try:
        parsed = json.loads(message)
    except json.JSONDecodeError as exc:
        raise GatewayError("message must be e2ee json") from exc
    if not isinstance(parsed, dict):
        raise GatewayError("message must be e2ee json")
    if not isinstance(parsed.get("ciphertext"), str) or not parsed.get("ciphertext"):
        raise GatewayError("message missing ciphertext")
    if not isinstance(parsed.get("iv"), str) or not parsed.get("iv"):
        raise GatewayError("message missing iv")
    return {"channel": channel, "message": message}


def validate_market_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise GatewayError("payload must be object")
    return dict(payload)


def validate_listing_payload(payload: dict[str, Any]) -> dict[str, Any]:
    payload = validate_market_payload(payload)
    for key in ("publisher_id", "sku", "title", "price"):
        if key not in payload:
            raise GatewayError(f"{key} required")
    payload["publisher_id"] = validate_address_text(payload["publisher_id"], "publisher_id")
    payload["sku"] = str(payload["sku"]).strip()
    payload["title"] = str(payload["title"]).strip()
    payload["price"] = require_int(payload, "price", min_value=1, max_value=_MAX_AMOUNT)
    if not payload["sku"] or len(payload["sku"]) > 64:
        raise GatewayError("sku invalid")
    if not payload["title"] or len(payload["title"]) > 128:
        raise GatewayError("title invalid")
    return payload


def validate_purchase_payload(payload: dict[str, Any]) -> dict[str, Any]:
    payload = validate_market_payload(payload)
    for key in ("listing_id", "buyer_id", "qty"):
        if key not in payload:
            raise GatewayError(f"{key} required")
    payload["listing_id"] = str(payload["listing_id"]).strip()
    payload["buyer_id"] = validate_address_text(payload["buyer_id"], "buyer_id")
    payload["qty"] = require_int(payload, "qty", min_value=1, max_value=100)
    if not payload["listing_id"] or len(payload["listing_id"]) > 128:
        raise GatewayError("listing_id invalid")
    return payload


def validate_entertainment_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise GatewayError("payload must be object")
    item_id = payload.get("item_id")
    mode = payload.get("mode")
    step = payload.get("step")
    if not isinstance(item_id, str) or not item_id:
        raise GatewayError("item_id required")
    if mode not in _ENTERTAINMENT_MODES:
        raise GatewayError("mode invalid")
    if not isinstance(step, int) or isinstance(step, bool):
        raise GatewayError("step must be int")
    return {"item_id": item_id, "mode": mode, "step": int(step)}
