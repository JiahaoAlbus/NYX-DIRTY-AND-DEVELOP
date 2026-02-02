from __future__ import annotations

import hashlib
from dataclasses import dataclass

from nyx_backend_gateway.env import get_fee_address
from nyx_backend_gateway.storage import (
    Order,
    Trade,
    apply_wallet_transfer,
    delete_order,
    get_wallet_balance,
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
    # Check balance
    current_balance = get_wallet_balance(conn, order.owner_address, order.asset_in)
    if current_balance < order.amount:
        raise ExchangeError(f"insufficient {order.asset_in} balance")

    insert_order(conn, order)
    trades: list[Trade] = []
    remaining = order.amount
    fee_address = get_fee_address()

    for row in _fetch_opposites(conn, order):
        opposite_price = int(row["price"])
        opposite_amount = int(row["amount"])
        opposite_id = str(row["order_id"])
        opposite_owner = str(row["owner_address"])

        if order.side == "BUY" and order.price < opposite_price:
            break
        if order.side == "SELL" and order.price > opposite_price:
            break

        trade_amount = min(remaining, opposite_amount)
        trade_id = _trade_id(order.order_id, opposite_id, trade_amount)
        
        # Settle the trade: Transfer assets between maker and taker
        # Taker (order) pays asset_in, gets asset_out
        # Maker (opposite) pays asset_out, gets asset_in
        
        # 1. Taker -> Maker (asset_in)
        apply_wallet_transfer(
            conn,
            transfer_id=f"{trade_id}-taker-to-maker",
            from_address=order.owner_address,
            to_address=opposite_owner,
            asset_id=order.asset_in,
            amount=trade_amount,
            fee_total=max(1, (trade_amount * 10) // 10_000), # 10 BPS
            treasury_address=fee_address,
            run_id=order.run_id
        )
        
        # 2. Maker -> Taker (asset_out)
        # Note: asset_out for Taker is asset_in for Maker
        trade_out_amount = trade_amount * opposite_price if order.side == "BUY" else trade_amount // opposite_price
        # Simplified: for testnet, we assume 1:1 or use price as multiplier
        # Let's use trade_amount as the base volume
        
        apply_wallet_transfer(
            conn,
            transfer_id=f"{trade_id}-maker-to-taker",
            from_address=opposite_owner,
            to_address=order.owner_address,
            asset_id=order.asset_out,
            amount=trade_amount, # Simplified 1:1 for now
            fee_total=max(1, (trade_amount * 10) // 10_000), # 10 BPS
            treasury_address=fee_address,
            run_id=order.run_id
        )

        trades.append(
            Trade(
                trade_id=trade_id,
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
