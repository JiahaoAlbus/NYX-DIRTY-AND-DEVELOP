from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ClientConfig:
    seed: int
    steps: int
    out_path: str


@dataclass(frozen=True)
class PoolSnapshot:
    pool_id: str
    asset_a: str
    asset_b: str
    reserve_a: int
    reserve_b: int
    total_lp: int

    def to_dict(self) -> dict:
        return {
            "pool_id": self.pool_id,
            "asset_a": self.asset_a,
            "asset_b": self.asset_b,
            "reserve_a": self.reserve_a,
            "reserve_b": self.reserve_b,
            "total_lp": self.total_lp,
        }


@dataclass(frozen=True)
class RouteStepView:
    pool_id: str
    asset_in: str
    amount_in: int
    min_out: int

    def to_dict(self) -> dict:
        return {
            "pool_id": self.pool_id,
            "asset_in": self.asset_in,
            "amount_in": self.amount_in,
            "min_out": self.min_out,
        }


@dataclass(frozen=True)
class StepResult:
    pool_id: str
    asset_in: str
    amount_in: int
    amount_out: int
    reserve_a: int
    reserve_b: int
    total_lp: int
    fee_charged: int

    def to_dict(self) -> dict:
        return {
            "pool_id": self.pool_id,
            "asset_in": self.asset_in,
            "amount_in": self.amount_in,
            "amount_out": self.amount_out,
            "reserve_a": self.reserve_a,
            "reserve_b": self.reserve_b,
            "total_lp": self.total_lp,
            "fee_charged": self.fee_charged,
        }


@dataclass(frozen=True)
class ClientReport:
    pool: PoolSnapshot
    steps: Tuple[RouteStepView, ...]
    step_panel: Tuple[StepResult, ...]
    state_hash_hex: str
    receipt_chain_hex: str

    def to_dict(self) -> dict:
        return {
            "pool": self.pool.to_dict(),
            "steps": [step.to_dict() for step in self.steps],
            "step_panel": [entry.to_dict() for entry in self.step_panel],
            "state_hash_hex": self.state_hash_hex,
            "receipt_chain_hex": self.receipt_chain_hex,
        }


@dataclass(frozen=True)
class ClientSummary:
    state_hash_hex: str
    receipt_chain_hex: str
    replay_ok: bool
