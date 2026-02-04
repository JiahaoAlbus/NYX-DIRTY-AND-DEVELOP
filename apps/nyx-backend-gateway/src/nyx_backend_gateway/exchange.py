from __future__ import annotations

import hashlib
from dataclasses import dataclass

from nyx_backend_gateway.env import get_fee_address
from nyx_backend_gateway.storage import (
    Order,
    Trade,
    apply_wallet_transfer,
    get_wallet_balance,
    insert_order,
    insert_trade,
    list_orders,
    update_order_status,
    update_order_amount,
)


class ExchangeError(ValueError):
    pass


@dataclass(frozen=True)
class ExchangeResult:
    order: Order
    trades: list[Trade]


def _trade_id(order_id: str, counter_id: str, amount: int) -> str:
    digest = hashlib.sha256(f"trade:{order_id}:{counter_id}:{amount}".encode("utf-8")).hexdigest()
    return f"trade-{digest[:16]}"


def _fetch_opposites(conn, order: Order) -> list[dict[str, object]]:
    if order.side == "BUY":
        return list_orders(
            conn,
            side="SELL",
            asset_in=order.asset_out,
            asset_out=order.asset_in,
            order_by="price ASC, order_id ASC",
        )
    return list_orders(
        conn,
        side="BUY",
        asset_in=order.asset_out,
        asset_out=order.asset_in,
        order_by="price DESC, order_id ASC",
    )


def place_order(conn, order: Order) -> ExchangeResult:
    # Check balance
    current_balance = get_wallet_balance(conn, order.owner_address, order.asset_in)
    if current_balance < order.amount:
        raise ExchangeError(f"insufficient {order.asset_in} balance")

    trades: list[Trade] = []
    remaining = order.amount
    fee_address = get_fee_address()

    try:
        insert_order(conn, order, commit=False)

        for row in _fetch_opposites(conn, order):
            opposite_price = int(row["price"])
            opposite_amount = int(row["amount"])
            opposite_id = str(row["order_id"])
            opposite_owner = str(row["owner_address"])

            if order.side == "BUY" and order.price < opposite_price:
                break
            if order.side == "SELL" and order.price > opposite_price:
                break

            # amount is in asset_in units for each order:
            # - BUY: asset_in is quote, amount is quote remaining
            # - SELL: asset_in is base, amount is base remaining
            # trades settle at maker price (opposite_price), quote per base.
            if opposite_price <= 0:
                continue

            if order.side == "BUY":
                buyer_quote_remaining = remaining
                seller_base_available = opposite_amount
                max_base = buyer_quote_remaining // opposite_price
                trade_base = min(seller_base_available, max_base)
                if trade_base <= 0:
                    break
                trade_quote = trade_base * opposite_price

                trade_id = _trade_id(order.order_id, opposite_id, trade_base)

                apply_wallet_transfer(
                    conn,
                    transfer_id=f"{trade_id}-taker-to-maker",
                    from_address=order.owner_address,
                    to_address=opposite_owner,
                    asset_id=order.asset_in,
                    amount=trade_quote,
                    fee_total=0,
                    treasury_address=fee_address,
                    run_id=order.run_id,
                    commit=False,
                )
                apply_wallet_transfer(
                    conn,
                    transfer_id=f"{trade_id}-maker-to-taker",
                    from_address=opposite_owner,
                    to_address=order.owner_address,
                    asset_id=order.asset_out,
                    amount=trade_base,
                    fee_total=0,
                    treasury_address=fee_address,
                    run_id=order.run_id,
                    commit=False,
                )

                trades.append(
                    Trade(
                        trade_id=f"{trade_id}-t",
                        order_id=order.order_id,
                        amount=trade_base,
                        price=opposite_price,
                        run_id=order.run_id,
                    )
                )
                insert_trade(conn, trades[-1], commit=False)
                insert_trade(
                    conn,
                    Trade(
                        trade_id=f"{trade_id}-m",
                        order_id=opposite_id,
                        amount=trade_base,
                        price=opposite_price,
                        run_id=order.run_id,
                    ),
                    commit=False,
                )

                # Update maker SELL order (base remaining)
                seller_remaining = seller_base_available - trade_base
                update_order_amount(conn, opposite_id, seller_remaining, commit=False)
                if seller_remaining == 0:
                    update_order_status(conn, opposite_id, "filled", commit=False)

                remaining = buyer_quote_remaining - trade_quote

            else:
                seller_base_remaining = remaining
                buyer_quote_available = opposite_amount
                max_base = buyer_quote_available // opposite_price
                trade_base = min(seller_base_remaining, max_base)
                if trade_base <= 0:
                    break
                trade_quote = trade_base * opposite_price

                trade_id = _trade_id(order.order_id, opposite_id, trade_base)

                apply_wallet_transfer(
                    conn,
                    transfer_id=f"{trade_id}-taker-to-maker",
                    from_address=order.owner_address,
                    to_address=opposite_owner,
                    asset_id=order.asset_in,
                    amount=trade_base,
                    fee_total=0,
                    treasury_address=fee_address,
                    run_id=order.run_id,
                    commit=False,
                )
                apply_wallet_transfer(
                    conn,
                    transfer_id=f"{trade_id}-maker-to-taker",
                    from_address=opposite_owner,
                    to_address=order.owner_address,
                    asset_id=order.asset_out,
                    amount=trade_quote,
                    fee_total=0,
                    treasury_address=fee_address,
                    run_id=order.run_id,
                    commit=False,
                )

                trades.append(
                    Trade(
                        trade_id=f"{trade_id}-t",
                        order_id=order.order_id,
                        amount=trade_base,
                        price=opposite_price,
                        run_id=order.run_id,
                    )
                )
                insert_trade(conn, trades[-1], commit=False)
                insert_trade(
                    conn,
                    Trade(
                        trade_id=f"{trade_id}-m",
                        order_id=opposite_id,
                        amount=trade_base,
                        price=opposite_price,
                        run_id=order.run_id,
                    ),
                    commit=False,
                )

                # Update maker BUY order (quote remaining)
                buyer_remaining = buyer_quote_available - trade_quote
                update_order_amount(conn, opposite_id, buyer_remaining, commit=False)
                if buyer_remaining == 0:
                    update_order_status(conn, opposite_id, "filled", commit=False)

                remaining = seller_base_remaining - trade_base

            if remaining == 0:
                break

        update_order_amount(conn, order.order_id, remaining, commit=False)
        if remaining == 0:
            update_order_status(conn, order.order_id, "filled", commit=False)
        conn.commit()
        return ExchangeResult(order=order, trades=trades)
    except Exception:
        conn.rollback()
        raise


def cancel_order(conn, order_id: str) -> None:
    update_order_status(conn, order_id, "cancelled")
