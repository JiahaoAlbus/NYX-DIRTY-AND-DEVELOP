from __future__ import annotations

from typing import cast

from nyx_backend_gateway.errors import GatewayError
from nyx_backend_gateway.fees import route_fee
from nyx_backend_gateway.identifiers import deterministic_id
from nyx_backend_gateway.storage import (
    Listing,
    Purchase,
    apply_wallet_transfer,
    get_wallet_balance,
    insert_fee_ledger,
    insert_listing,
    insert_purchase,
    list_listings,
    load_by_id,
)
from nyx_backend_gateway.validation import validate_listing_payload, validate_purchase_payload


def list_active_listings(conn, limit: int = 100, offset: int = 0) -> list[dict[str, object]]:
    return list_listings(conn, limit=limit, offset=offset)


def search_listings(conn, q: str, limit: int = 100, offset: int = 0) -> list[dict[str, object]]:
    query = (q or "").strip()
    if not query:
        return list_listings(conn, limit=limit, offset=offset)
    if len(query) > 64:
        raise GatewayError("q too long")
    lim = int(limit)
    off = int(offset)
    if lim < 1 or lim > 200:
        raise GatewayError("limit out of bounds")
    if off < 0:
        raise GatewayError("offset out of bounds")
    pattern = f"%{query}%"
    rows = conn.execute(
        "SELECT * FROM listings WHERE status = 'active' AND (sku LIKE ? OR title LIKE ?) "
        "ORDER BY listing_id ASC LIMIT ? OFFSET ?",
        (pattern, pattern, lim, off),
    ).fetchall()
    return [{col: row[col] for col in row.keys()} for row in rows]


def publish_listing(conn, run_id: str, payload: dict[str, object], caller_wallet_address: str | None) -> None:
    validated = validate_listing_payload(payload)
    if caller_wallet_address and validated.get("publisher_id") != caller_wallet_address:
        raise GatewayError("publisher_id mismatch")
    fee_record = route_fee("marketplace", "listing_publish", validated, run_id)
    if caller_wallet_address:
        nyxt_balance = get_wallet_balance(conn, caller_wallet_address, "NYXT")
        if nyxt_balance < int(fee_record.total_paid):
            raise GatewayError("insufficient NYXT balance for fee")
    insert_listing(
        conn,
        Listing(
            listing_id=deterministic_id("listing", run_id),
            publisher_id=validated["publisher_id"],
            sku=validated["sku"],
            title=validated["title"],
            price=validated["price"],
            status="active",
            run_id=run_id,
        ),
    )
    if caller_wallet_address:
        apply_wallet_transfer(
            conn,
            transfer_id=deterministic_id("fee", run_id),
            from_address=caller_wallet_address,
            to_address=fee_record.fee_address,
            asset_id="NYXT",
            amount=0,
            fee_total=fee_record.total_paid,
            treasury_address=fee_record.fee_address,
            run_id=run_id,
        )
        insert_fee_ledger(conn, fee_record)


def purchase_listing(conn, run_id: str, payload: dict[str, object], caller_wallet_address: str | None) -> None:
    validated = validate_purchase_payload(payload)
    if caller_wallet_address and validated.get("buyer_id") != caller_wallet_address:
        raise GatewayError("buyer_id mismatch")
    listing_record = load_by_id(conn, "listings", "listing_id", validated["listing_id"])
    if listing_record is None:
        raise GatewayError("listing_id not found")
    if str(listing_record.get("status") or "active") != "active":
        raise GatewayError("listing not available")

    total_price = int(cast(int, listing_record["price"])) * int(cast(int, validated["qty"]))
    fee_record = route_fee("marketplace", "purchase_listing", validated, run_id)
    if caller_wallet_address:
        nyxt_balance = get_wallet_balance(conn, caller_wallet_address, "NYXT")
        required = total_price + int(fee_record.total_paid)
        if nyxt_balance < required:
            raise GatewayError("insufficient NYXT balance for amount + fee")

    apply_wallet_transfer(
        conn,
        transfer_id=deterministic_id("purchase-xfer", run_id),
        from_address=validated["buyer_id"],
        to_address=str(listing_record["publisher_id"]),
        asset_id="NYXT",
        amount=total_price,
        fee_total=int(fee_record.total_paid),
        treasury_address=fee_record.fee_address,
        run_id=run_id,
    )

    insert_purchase(
        conn,
        Purchase(
            purchase_id=deterministic_id("purchase", run_id),
            listing_id=validated["listing_id"],
            buyer_id=validated["buyer_id"],
            qty=validated["qty"],
            run_id=run_id,
        ),
    )
    conn.execute("UPDATE listings SET status = 'sold' WHERE listing_id = ?", (validated["listing_id"],))
    conn.commit()
    insert_fee_ledger(conn, fee_record)
