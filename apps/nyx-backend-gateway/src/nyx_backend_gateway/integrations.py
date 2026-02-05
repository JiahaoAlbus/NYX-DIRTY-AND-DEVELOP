from __future__ import annotations

import json
import re
import socket
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from nyx_backend_gateway.env import get_0x_api_key, get_jupiter_api_key, get_magic_eden_api_key
from nyx_backend_gateway.gateway import GatewayApiError


_DEFAULT_TIMEOUT_SECONDS = 10
_MAX_UPSTREAM_BYTES = 250_000

_SAFE_TEXT = re.compile(r"^[A-Za-z0-9:/_.-]{1,256}$")
_SAFE_HEX_OR_WORD = re.compile(r"^[A-Za-z0-9_-]{1,256}$")
_SAFE_SOL_MINT = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,64}$")
_SAFE_EVM_ADDRESS = re.compile(r"^0x[a-fA-F0-9]{40}$")
_SAFE_ME_SYMBOL = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _read_limited(resp, limit: int) -> bytes:
    data = resp.read(limit + 1)
    if len(data) > limit:
        raise GatewayApiError(
            "UPSTREAM_RESPONSE_TOO_LARGE",
            "upstream response too large",
            http_status=502,
            details={"limit_bytes": limit},
        )
    return data


def _safe_snippet(raw: bytes) -> str:
    try:
        text = raw.decode("utf-8", errors="replace")
    except Exception:
        return ""
    text = text.replace("\n", "\\n").replace("\r", "\\r")
    if len(text) > 4000:
        return text[:4000] + "…"
    return text


def _http_get_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    req = Request(url, headers=headers, method="GET")
    try:
        with urlopen(req, timeout=_DEFAULT_TIMEOUT_SECONDS) as resp:
            status = getattr(resp, "status", 200)
            body = _read_limited(resp, _MAX_UPSTREAM_BYTES)
    except HTTPError as exc:
        body = b""
        try:
            body = _read_limited(exc, _MAX_UPSTREAM_BYTES)
        except Exception:
            body = b""
        raise GatewayApiError(
            "UPSTREAM_HTTP_ERROR",
            f"upstream http error {exc.code}",
            http_status=502,
            details={"status": int(exc.code), "body": _safe_snippet(body)},
        ) from exc
    except URLError as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, socket.timeout):
            raise GatewayApiError("UPSTREAM_TIMEOUT", "upstream timeout", http_status=504) from exc
        raise GatewayApiError("UPSTREAM_UNAVAILABLE", "upstream unavailable", http_status=502) from exc
    except socket.timeout as exc:
        raise GatewayApiError("UPSTREAM_TIMEOUT", "upstream timeout", http_status=504) from exc

    try:
        parsed = json.loads(body.decode("utf-8"))
    except Exception as exc:
        raise GatewayApiError(
            "UPSTREAM_BAD_JSON",
            "upstream returned invalid json",
            http_status=502,
            details={"status": int(status), "body": _safe_snippet(body)},
        ) from exc
    if not isinstance(parsed, dict):
        raise GatewayApiError(
            "UPSTREAM_BAD_JSON",
            "upstream returned non-object json",
            http_status=502,
            details={"status": int(status)},
        )
    return {"status": int(status), "data": parsed}


def _http_get_json_any(url: str, headers: dict[str, str]) -> dict[str, Any]:
    req = Request(url, headers=headers, method="GET")
    try:
        with urlopen(req, timeout=_DEFAULT_TIMEOUT_SECONDS) as resp:
            status = getattr(resp, "status", 200)
            body = _read_limited(resp, _MAX_UPSTREAM_BYTES)
    except HTTPError as exc:
        body = b""
        try:
            body = _read_limited(exc, _MAX_UPSTREAM_BYTES)
        except Exception:
            body = b""
        raise GatewayApiError(
            "UPSTREAM_HTTP_ERROR",
            f"upstream http error {exc.code}",
            http_status=502,
            details={"status": int(exc.code), "body": _safe_snippet(body)},
        ) from exc
    except URLError as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, socket.timeout):
            raise GatewayApiError("UPSTREAM_TIMEOUT", "upstream timeout", http_status=504) from exc
        raise GatewayApiError("UPSTREAM_UNAVAILABLE", "upstream unavailable", http_status=502) from exc
    except socket.timeout as exc:
        raise GatewayApiError("UPSTREAM_TIMEOUT", "upstream timeout", http_status=504) from exc

    try:
        parsed = json.loads(body.decode("utf-8"))
    except Exception as exc:
        raise GatewayApiError(
            "UPSTREAM_BAD_JSON",
            "upstream returned invalid json",
            http_status=502,
            details={"status": int(status), "body": _safe_snippet(body)},
        ) from exc
    return {"status": int(status), "data": parsed}


def _require_nonempty_str(value: str, *, name: str, pattern: re.Pattern[str] | None = None) -> str:
    raw = (value or "").strip()
    if not raw:
        raise GatewayApiError("PARAM_REQUIRED", f"{name} required", http_status=400, details={"param": name})
    if len(raw) > 256:
        raise GatewayApiError("PARAM_INVALID", f"{name} too long", http_status=400, details={"param": name})
    if pattern is not None and not pattern.fullmatch(raw):
        raise GatewayApiError("PARAM_INVALID", f"{name} invalid", http_status=400, details={"param": name})
    return raw


def _optional_int(value: str | None, *, name: str, min_value: int | None = None, max_value: int | None = None) -> int | None:
    if value is None:
        return None
    raw = value.strip()
    if not raw:
        return None
    try:
        parsed = int(raw)
    except ValueError as exc:
        raise GatewayApiError("PARAM_INVALID", f"{name} must be int", http_status=400, details={"param": name}) from exc
    if min_value is not None and parsed < min_value:
        raise GatewayApiError("PARAM_INVALID", f"{name} out of bounds", http_status=400, details={"param": name})
    if max_value is not None and parsed > max_value:
        raise GatewayApiError("PARAM_INVALID", f"{name} out of bounds", http_status=400, details={"param": name})
    return parsed


def _0x_base_url(network: str | None, chain_id: int | None) -> str:
    if network:
        network = network.strip().lower()
    network_map = {
        "ethereum": "https://api.0x.org",
        "mainnet": "https://api.0x.org",
        "polygon": "https://api.0x.org",
        "optimism": "https://api.0x.org",
        "arbitrum": "https://api.0x.org",
        "base": "https://api.0x.org",
        "bsc": "https://api.0x.org",
        "avalanche": "https://api.0x.org",
    }
    chain_map = {
        1: "https://api.0x.org",
        10: "https://api.0x.org",
        56: "https://api.0x.org",
        137: "https://api.0x.org",
        42161: "https://api.0x.org",
        8453: "https://api.0x.org",
        43114: "https://api.0x.org",
    }
    if network:
        base = network_map.get(network)
        if not base:
            raise GatewayApiError(
                "PARAM_INVALID",
                "network not supported",
                http_status=400,
                details={"param": "network", "supported": sorted(network_map.keys())},
            )
        return base
    if chain_id is not None:
        base = chain_map.get(chain_id)
        if not base:
            raise GatewayApiError(
                "PARAM_INVALID",
                "chain_id not supported",
                http_status=400,
                details={"param": "chain_id", "supported": sorted(chain_map.keys())},
            )
        return base
    return "https://api.0x.org"


def quote_0x(*, network: str | None, chain_id: int | None, sell_token: str, buy_token: str, sell_amount: str | None, buy_amount: str | None, taker_address: str | None, slippage_bps: int | None) -> dict[str, Any]:
    api_key = get_0x_api_key()
    if not api_key:
        raise GatewayApiError("INTEGRATION_DISABLED", "0x integration disabled (missing api key)", http_status=503)

    # 0x v2 (permit2) requires chainId + token addresses + taker address.
    if network:
        net = network.strip().lower()
        default_chain_map = {
            "ethereum": 1,
            "mainnet": 1,
            "polygon": 137,
            "optimism": 10,
            "arbitrum": 42161,
            "base": 8453,
            "bsc": 56,
            "avalanche": 43114,
        }
        inferred = default_chain_map.get(net)
        if chain_id is None and inferred is not None:
            chain_id = inferred
        if chain_id is not None and inferred is not None and chain_id != inferred:
            raise GatewayApiError(
                "PARAM_INVALID",
                "network and chain_id mismatch",
                http_status=400,
                details={"param": "chain_id", "network": net, "expected": inferred, "actual": chain_id},
            )
    if chain_id is None:
        chain_id = 1

    sell_token = _require_nonempty_str(sell_token, name="sell_token", pattern=_SAFE_EVM_ADDRESS)
    buy_token = _require_nonempty_str(buy_token, name="buy_token", pattern=_SAFE_EVM_ADDRESS)

    sell_amount = (sell_amount or "").strip() or None
    buy_amount = (buy_amount or "").strip() or None
    if not sell_amount and not buy_amount:
        raise GatewayApiError(
            "PARAM_REQUIRED",
            "sell_amount or buy_amount required",
            http_status=400,
            details={"param": "sell_amount|buy_amount"},
        )
    if sell_amount and buy_amount:
        raise GatewayApiError(
            "PARAM_INVALID",
            "provide only one of sell_amount or buy_amount",
            http_status=400,
            details={"param": "sell_amount|buy_amount"},
        )
    if sell_amount is not None and not sell_amount.isdigit():
        raise GatewayApiError("PARAM_INVALID", "sell_amount must be integer string", http_status=400, details={"param": "sell_amount"})
    if buy_amount is not None and not buy_amount.isdigit():
        raise GatewayApiError("PARAM_INVALID", "buy_amount must be integer string", http_status=400, details={"param": "buy_amount"})

    taker_address = (taker_address or "").strip() or None
    if taker_address is None:
        raise GatewayApiError("PARAM_REQUIRED", "taker_address required for 0x v2", http_status=400, details={"param": "taker_address"})
    if not _SAFE_EVM_ADDRESS.fullmatch(taker_address):
        raise GatewayApiError("PARAM_INVALID", "taker_address invalid", http_status=400, details={"param": "taker_address"})
    if int(taker_address, 16) <= 0xFFFF:
        raise GatewayApiError(
            "PARAM_INVALID",
            "taker_address too low (must be > 0x000000000000000000000000000000000000ffff)",
            http_status=400,
            details={"param": "taker_address"},
        )

    params: dict[str, str] = {"chainId": str(chain_id), "sellToken": sell_token, "buyToken": buy_token, "taker": taker_address}
    if sell_amount is not None:
        params["sellAmount"] = sell_amount
    if buy_amount is not None:
        params["buyAmount"] = buy_amount
    if slippage_bps is not None:
        if slippage_bps < 0 or slippage_bps > 10_000:
            raise GatewayApiError("PARAM_INVALID", "slippage_bps out of bounds", http_status=400, details={"param": "slippage_bps"})
        params["slippagePercentage"] = f"{slippage_bps / 10_000:.6f}".rstrip("0").rstrip(".")

    base = _0x_base_url(network, chain_id)
    url = f"{base}/swap/permit2/quote?{urlencode(params)}"
    result = _http_get_json(
        url,
        headers={
            "accept": "application/json",
            "0x-api-key": api_key,
            "0x-version": "v2",
            "user-agent": "NYXGateway/2.0",
        },
    )
    return {"provider": "0x", "request": {"network": network, "chain_id": chain_id, **params}, **result}


def quote_jupiter(
    *,
    input_mint: str,
    output_mint: str,
    amount: str,
    slippage_bps: int | None,
    swap_mode: str | None,
) -> dict[str, Any]:
    api_key = get_jupiter_api_key()
    if not api_key:
        raise GatewayApiError("INTEGRATION_DISABLED", "jupiter integration disabled (missing api key)", http_status=503)

    input_mint = _require_nonempty_str(input_mint, name="input_mint", pattern=_SAFE_SOL_MINT)
    output_mint = _require_nonempty_str(output_mint, name="output_mint", pattern=_SAFE_SOL_MINT)
    amount = _require_nonempty_str(amount, name="amount", pattern=_SAFE_HEX_OR_WORD)
    if not amount.isdigit():
        raise GatewayApiError("PARAM_INVALID", "amount must be integer string", http_status=400, details={"param": "amount"})

    params: dict[str, str] = {"inputMint": input_mint, "outputMint": output_mint, "amount": amount}
    if slippage_bps is not None:
        if slippage_bps < 0 or slippage_bps > 10_000:
            raise GatewayApiError("PARAM_INVALID", "slippage_bps out of bounds", http_status=400, details={"param": "slippage_bps"})
        params["slippageBps"] = str(slippage_bps)
    if swap_mode:
        swap_mode = swap_mode.strip()
        if swap_mode and not _SAFE_HEX_OR_WORD.fullmatch(swap_mode):
            raise GatewayApiError("PARAM_INVALID", "swap_mode invalid", http_status=400, details={"param": "swap_mode"})
        if swap_mode:
            params["swapMode"] = swap_mode

    url = f"https://api.jup.ag/swap/v1/quote?{urlencode(params)}"
    result = _http_get_json(
        url,
        headers={
            "accept": "application/json",
            "x-api-key": api_key,
            "user-agent": "NYXGateway/2.0",
        },
    )
    return {"provider": "jupiter", "request": params, **result}


def _magic_eden_headers() -> dict[str, str]:
    api_key = get_magic_eden_api_key()
    headers = {
        "accept": "application/json",
        "user-agent": "NYXGateway/2.0",
    }
    if api_key:
        headers["authorization"] = api_key
    return headers


def magic_eden_solana_collections(*, limit: int | None, offset: int | None) -> dict[str, Any]:
    params: dict[str, str] = {}
    if limit is not None:
        params["limit"] = str(_optional_int(str(limit), name="limit", min_value=1, max_value=200))
    if offset is not None:
        params["offset"] = str(_optional_int(str(offset), name="offset", min_value=0, max_value=1_000_000))
    url = "https://api-mainnet.magiceden.dev/v2/collections"
    if params:
        url = f"{url}?{urlencode(params)}"
    result = _http_get_json_any(url, headers=_magic_eden_headers())
    return {"provider": "magic_eden", "network": "solana", "endpoint": "collections", **result}


def magic_eden_solana_collection_listings(*, symbol: str, limit: int | None, offset: int | None) -> dict[str, Any]:
    symbol = _require_nonempty_str(symbol, name="symbol", pattern=_SAFE_ME_SYMBOL)
    params: dict[str, str] = {}
    if limit is not None:
        params["limit"] = str(_optional_int(str(limit), name="limit", min_value=1, max_value=200))
    if offset is not None:
        params["offset"] = str(_optional_int(str(offset), name="offset", min_value=0, max_value=1_000_000))
    url = f"https://api-mainnet.magiceden.dev/v2/collections/{symbol}/listings"
    if params:
        url = f"{url}?{urlencode(params)}"
    result = _http_get_json_any(url, headers=_magic_eden_headers())
    return {"provider": "magic_eden", "network": "solana", "endpoint": "collection_listings", "symbol": symbol, **result}


def magic_eden_solana_token(*, mint: str) -> dict[str, Any]:
    mint = _require_nonempty_str(mint, name="mint", pattern=_SAFE_SOL_MINT)
    url = f"https://api-mainnet.magiceden.dev/v2/tokens/{mint}"
    result = _http_get_json_any(url, headers=_magic_eden_headers())
    return {"provider": "magic_eden", "network": "solana", "endpoint": "token", "mint": mint, **result}
