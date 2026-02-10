#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class Event:
    flow: str
    base_amount: int
    protocol_fee: int
    platform_fee: int
    total_fee: int


def clamp_int(value: int, minimum: int = 1) -> int:
    return value if value >= minimum else minimum


def fee_from_base(
    base_amount: int,
    *,
    platform_fee_bps: int,
    protocol_fee_bps: int,
    protocol_fee_min: int,
) -> tuple[int, int, int]:
    platform_fee = 0
    if platform_fee_bps > 0:
        platform_fee = clamp_int((base_amount * platform_fee_bps) // 10_000, 1)
    protocol_fee = (base_amount * protocol_fee_bps) // 10_000 if protocol_fee_bps > 0 else 0
    protocol_fee = clamp_int(protocol_fee, protocol_fee_min)
    total_fee = platform_fee + protocol_fee
    if total_fee <= 0:
        total_fee = 1
    return protocol_fee, platform_fee, total_fee


def simulate_trades(
    rng: random.Random,
    count: int,
    amount_min: int,
    amount_max: int,
    price_min: int,
    price_max: int,
    *,
    platform_fee_bps: int,
    protocol_fee_bps: int,
    protocol_fee_min: int,
) -> list[Event]:
    events: list[Event] = []
    for _ in range(count):
        amount = rng.randint(amount_min, amount_max)
        price = rng.randint(price_min, price_max)
        base = amount * price
        protocol_fee, platform_fee, total_fee = fee_from_base(
            base,
            platform_fee_bps=platform_fee_bps,
            protocol_fee_bps=protocol_fee_bps,
            protocol_fee_min=protocol_fee_min,
        )
        events.append(
            Event(
                flow="trade",
                base_amount=base,
                protocol_fee=protocol_fee,
                platform_fee=platform_fee,
                total_fee=total_fee,
            )
        )
    return events


def simulate_airdrops(
    rng: random.Random,
    count: int,
    amount_min: int,
    amount_max: int,
    *,
    platform_fee_bps: int,
    protocol_fee_bps: int,
    protocol_fee_min: int,
) -> list[Event]:
    events: list[Event] = []
    for _ in range(count):
        amount = rng.randint(amount_min, amount_max)
        base = amount
        protocol_fee, platform_fee, total_fee = fee_from_base(
            base,
            platform_fee_bps=platform_fee_bps,
            protocol_fee_bps=protocol_fee_bps,
            protocol_fee_min=protocol_fee_min,
        )
        events.append(
            Event(
                flow="airdrop",
                base_amount=base,
                protocol_fee=protocol_fee,
                platform_fee=platform_fee,
                total_fee=total_fee,
            )
        )
    return events


def summarize(events: Iterable[Event]) -> dict[str, float]:
    values = list(events)
    if not values:
        return {
            "count": 0,
            "base": 0,
            "protocol": 0,
            "platform": 0,
            "total": 0,
            "avg": 0,
            "min": 0,
            "max": 0,
        }
    total_base = sum(e.base_amount for e in values)
    total_protocol = sum(e.protocol_fee for e in values)
    total_platform = sum(e.platform_fee for e in values)
    total_fee = sum(e.total_fee for e in values)
    min_fee = min(e.total_fee for e in values)
    max_fee = max(e.total_fee for e in values)
    avg_fee = total_fee / len(values)
    return {
        "count": len(values),
        "base": total_base,
        "protocol": total_protocol,
        "platform": total_platform,
        "total": total_fee,
        "avg": avg_fee,
        "min": min_fee,
        "max": max_fee,
    }


def ascii_hist(values: list[int], bins: int = 10, width: int = 32) -> str:
    if not values:
        return "(no data)"
    vmin = min(values)
    vmax = max(values)
    if vmin == vmax:
        return f"{vmin}: " + ("#" * width)
    step = (vmax - vmin) / bins
    buckets = [0 for _ in range(bins)]
    for v in values:
        idx = int((v - vmin) / step)
        if idx >= bins:
            idx = bins - 1
        buckets[idx] += 1
    max_bucket = max(buckets)
    lines = []
    for i, count in enumerate(buckets):
        lo = vmin + step * i
        hi = vmin + step * (i + 1)
        bar = "#" * int(math.ceil((count / max_bucket) * width)) if max_bucket else ""
        lines.append(f"{lo:>8.2f} - {hi:>8.2f} | {bar} ({count})")
    return "\n".join(lines)


def write_outputs(out_dir: Path, events: list[Event], summary: dict[str, dict[str, float]]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "economics_events.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["flow", "base_amount", "protocol_fee", "platform_fee", "total_fee"])
        for e in events:
            writer.writerow([e.flow, e.base_amount, e.protocol_fee, e.platform_fee, e.total_fee])

    summary_path = out_dir / "economics_summary.md"
    with summary_path.open("w", encoding="utf-8") as handle:
        handle.write("# NYX Economics Simulation Summary\n\n")
        handle.write("| Flow | Count | Base Sum | Protocol Fee | Platform Fee | Total Fee | Avg Fee | Min | Max |\n")
        handle.write("|---|---:|---:|---:|---:|---:|---:|---:|---:|\n")
        for flow, stats in summary.items():
            handle.write(
                f"| {flow} | {int(stats['count'])} | {int(stats['base'])} | {int(stats['protocol'])} | "
                f"{int(stats['platform'])} | {int(stats['total'])} | {stats['avg']:.2f} | "
                f"{int(stats['min'])} | {int(stats['max'])} |\n"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="NYX economic simulation (trade + airdrop flows).")
    parser.add_argument("--seed", type=int, default=123, help="Deterministic RNG seed.")
    parser.add_argument("--trades", type=int, default=200, help="Number of trade events to simulate.")
    parser.add_argument("--airdrop-claims", type=int, default=50, help="Number of airdrop claims to simulate.")
    parser.add_argument("--trade-amount-min", type=int, default=10)
    parser.add_argument("--trade-amount-max", type=int, default=500)
    parser.add_argument("--trade-price-min", type=int, default=1)
    parser.add_argument("--trade-price-max", type=int, default=20)
    parser.add_argument("--airdrop-amount-min", type=int, default=100)
    parser.add_argument("--airdrop-amount-max", type=int, default=1000)
    parser.add_argument("--platform-fee-bps", type=int, default=10)
    parser.add_argument("--protocol-fee-bps", type=int, default=0)
    parser.add_argument("--protocol-fee-min", type=int, default=1)
    parser.add_argument("--out-dir", type=str, default="", help="Optional output directory for CSV/summary files.")

    args = parser.parse_args()

    rng = random.Random(args.seed)
    trade_events = simulate_trades(
        rng,
        args.trades,
        args.trade_amount_min,
        args.trade_amount_max,
        args.trade_price_min,
        args.trade_price_max,
        platform_fee_bps=args.platform_fee_bps,
        protocol_fee_bps=args.protocol_fee_bps,
        protocol_fee_min=args.protocol_fee_min,
    )
    airdrop_events = simulate_airdrops(
        rng,
        args.airdrop_claims,
        args.airdrop_amount_min,
        args.airdrop_amount_max,
        platform_fee_bps=args.platform_fee_bps,
        protocol_fee_bps=args.protocol_fee_bps,
        protocol_fee_min=args.protocol_fee_min,
    )
    events = trade_events + airdrop_events

    summary = {
        "trade": summarize(trade_events),
        "airdrop": summarize(airdrop_events),
        "total": summarize(events),
    }

    print("# NYX Economics Simulation")
    print(f"seed={args.seed} trades={args.trades} airdrop_claims={args.airdrop_claims}")
    print(f"platform_fee_bps={args.platform_fee_bps} protocol_fee_bps={args.protocol_fee_bps} protocol_fee_min={args.protocol_fee_min}")
    print()
    print("| Flow | Count | Base Sum | Protocol Fee | Platform Fee | Total Fee | Avg Fee | Min | Max |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for flow, stats in summary.items():
        print(
            f"| {flow} | {int(stats['count'])} | {int(stats['base'])} | {int(stats['protocol'])} | "
            f"{int(stats['platform'])} | {int(stats['total'])} | {stats['avg']:.2f} | "
            f"{int(stats['min'])} | {int(stats['max'])} |"
        )

    print("\n## Total Fee Distribution (ASCII)\n")
    print(ascii_hist([e.total_fee for e in events]))

    if args.out_dir:
        write_outputs(Path(args.out_dir), events, summary)
        print(f"\nOutputs written to: {args.out_dir}")


if __name__ == "__main__":
    main()
