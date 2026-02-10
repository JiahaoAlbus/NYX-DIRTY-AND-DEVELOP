from __future__ import annotations

import hashlib


def deterministic_id(prefix: str, run_id: str) -> str:
    digest = hashlib.sha256(f"{prefix}:{run_id}".encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"


def order_id(run_id: str) -> str:
    return deterministic_id("order", run_id)


def receipt_id(run_id: str) -> str:
    return deterministic_id("receipt", run_id)


def wallet_address(account_id: str) -> str:
    digest = hashlib.sha256(f"wallet:{account_id}".encode("utf-8")).hexdigest()
    return f"wallet-{digest[:16]}"
