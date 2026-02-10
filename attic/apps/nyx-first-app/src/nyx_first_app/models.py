from __future__ import annotations

from dataclasses import dataclass


class AppError(ValueError):
    pass


@dataclass(frozen=True)
class AppConfig:
    seed: int
    out_path: str
    action: str = "post_note"

    def __post_init__(self) -> None:
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise AppError("seed must be int")
        if not isinstance(self.out_path, str) or not self.out_path:
            raise AppError("out_path must be non-empty string")
        if not isinstance(self.action, str) or not self.action:
            raise AppError("action must be non-empty string")


@dataclass(frozen=True)
class AppSummary:
    action: str
    fee_total: int
    tx_hash_prefix: str
    block_hash_prefix: str
    state_root_prefix: str
    receipt_hash_prefix: str
    replay_ok: bool

    def __post_init__(self) -> None:
        if not isinstance(self.action, str) or not self.action:
            raise AppError("action must be non-empty string")
        if not isinstance(self.fee_total, int) or isinstance(self.fee_total, bool):
            raise AppError("fee_total must be int")
        for field_name, value in (
            ("tx_hash_prefix", self.tx_hash_prefix),
            ("block_hash_prefix", self.block_hash_prefix),
            ("state_root_prefix", self.state_root_prefix),
            ("receipt_hash_prefix", self.receipt_hash_prefix),
        ):
            if not isinstance(value, str) or not value:
                raise AppError(f"{field_name} must be non-empty string")
        if not isinstance(self.replay_ok, bool):
            raise AppError("replay_ok must be bool")
