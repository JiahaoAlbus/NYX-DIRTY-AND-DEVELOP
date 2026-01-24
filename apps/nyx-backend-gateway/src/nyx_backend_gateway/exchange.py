from __future__ import annotations

import hashlib
from dataclasses import dataclass

from nyx_backend_gateway.storage import (
    Order,
    Trade,
    delete_order,
    insert_order,
    insert_trade,
    list_orders,
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
    insert_order(conn, order)
    trades: list[Trade] = []
    remaining = order.amount
    for row in _fetch_opposites(conn, order):
        opposite_price = int(row["price"])
        opposite_amount = int(row["amount"])
        opposite_id = str(row["order_id"])
        if order.side == "BUY" and order.price < opposite_price:
            break
        if order.side == "SELL" and order.price > opposite_price:
            break
        trade_amount = min(remaining, opposite_amount)
        trades.append(
            Trade(
                trade_id=_trade_id(order.order_id, opposite_id, trade_amount),
                order_id=order.order_id,
                amount=trade_amount,
                price=opposite_price,
                run_id=order.run_id,
            )
        )
        insert_trade(conn, trades[-1])
        if trade_amount == opposite_amount:
            delete_order(conn, opposite_id)
        else:
            update_order_amount(conn, opposite_id, opposite_amount - trade_amount)
        remaining -= trade_amount
        if remaining == 0:
            break
    if remaining == 0:
        delete_order(conn, order.order_id)
    elif remaining != order.amount:
        update_order_amount(conn, order.order_id, remaining)
    return ExchangeResult(order=order, trades=trades)


def cancel_order(conn, order_id: str) -> None:
    delete_order(conn, order_id)
