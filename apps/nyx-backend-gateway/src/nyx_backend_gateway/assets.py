from __future__ import annotations

_SUPPORTED_ASSETS: dict[str, dict[str, object]] = {
    "NYXT": {"name": "NYX Testnet Token"},
    "ECHO": {"name": "Echo Test Asset"},
    "USDX": {"name": "NYX Testnet Stable"},
}


def supported_assets() -> list[dict[str, object]]:
    return [{"asset_id": asset_id, **meta} for asset_id, meta in sorted(_SUPPORTED_ASSETS.items())]


def is_supported_asset(asset_id: str) -> bool:
    return asset_id in _SUPPORTED_ASSETS
