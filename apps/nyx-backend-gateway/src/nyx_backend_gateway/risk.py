from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Literal

from nyx_backend_gateway.errors import GatewayApiError
from nyx_backend_gateway.settings import get_settings

logger = logging.getLogger("nyx-risk")

RiskMode = Literal["off", "monitor", "enforce"]


@dataclass(frozen=True)
class RiskLimit:
    max_count: int | None = None
    max_amount: int | None = None
    window_seconds: int = 60


@dataclass(frozen=True)
class RiskConfig:
    mode: RiskMode
    global_paused: bool
    global_limit: RiskLimit
    account_limit: RiskLimit
    ip_limit: RiskLimit
    action_limits: dict[str, RiskLimit]
    breaker_errors_per_min: int
    breaker_window_seconds: int


class RiskEngine:
    def __init__(self, config: RiskConfig) -> None:
        self._config = config
        self._counters: dict[str, tuple[int, int, int]] = {}
        self._error_counters: dict[str, tuple[int, int]] = {}
        self._breaker_windows: dict[str, int] = {}

    @classmethod
    def from_settings(cls) -> "RiskEngine":
        settings = get_settings()
        config = RiskConfig(
            mode=settings.risk_mode,
            global_paused=settings.risk_global_mutations_paused,
            global_limit=RiskLimit(
                max_count=settings.risk_global_max_per_min,
                max_amount=settings.risk_global_max_amount_per_min,
                window_seconds=60,
            ),
            account_limit=RiskLimit(
                max_count=settings.risk_account_max_per_min,
                max_amount=settings.risk_account_max_amount_per_min,
                window_seconds=60,
            ),
            ip_limit=RiskLimit(
                max_count=settings.risk_ip_max_per_min,
                max_amount=settings.risk_ip_max_amount_per_min,
                window_seconds=60,
            ),
            action_limits={
                "wallet_faucet": RiskLimit(
                    max_count=settings.risk_faucet_max_per_min,
                    max_amount=settings.risk_max_faucet_amount,
                    window_seconds=60,
                ),
                "wallet_transfer": RiskLimit(
                    max_count=settings.risk_transfer_max_per_min,
                    max_amount=settings.risk_max_transfer_amount,
                    window_seconds=60,
                ),
                "wallet_airdrop": RiskLimit(
                    max_count=settings.risk_airdrop_max_per_min,
                    max_amount=settings.risk_max_airdrop_amount,
                    window_seconds=60,
                ),
                "exchange_order": RiskLimit(
                    max_count=settings.risk_exchange_orders_per_min,
                    max_amount=settings.risk_max_order_notional,
                    window_seconds=60,
                ),
                "exchange_cancel": RiskLimit(
                    max_count=settings.risk_exchange_cancels_per_min,
                    max_amount=None,
                    window_seconds=60,
                ),
                "marketplace_purchase": RiskLimit(
                    max_count=settings.risk_marketplace_orders_per_min,
                    max_amount=settings.risk_max_store_notional,
                    window_seconds=60,
                ),
                "chat_message": RiskLimit(
                    max_count=settings.risk_chat_messages_per_min,
                    max_amount=None,
                    window_seconds=60,
                ),
            },
            breaker_errors_per_min=settings.risk_breaker_errors_per_min,
            breaker_window_seconds=settings.risk_breaker_window_seconds,
        )
        return cls(config)

    def _window(self, window_seconds: int) -> int:
        now = int(time.time())
        return now // window_seconds

    def _bump_counter(self, key: str, limit: RiskLimit, amount: int) -> tuple[int, int]:
        window_id = self._window(limit.window_seconds)
        count, total_amount, stored_window = self._counters.get(key, (0, 0, window_id))
        if stored_window != window_id:
            count, total_amount = 0, 0
        count += 1
        total_amount += max(amount, 0)
        self._counters[key] = (count, total_amount, window_id)
        return count, total_amount

    def _check_limit(self, label: str, key: str, limit: RiskLimit, amount: int) -> None:
        if limit.max_count is None and limit.max_amount is None:
            return
        count, total_amount = self._bump_counter(key, limit, amount)
        if limit.max_count is not None and count > limit.max_count:
            self._deny(label, "count", limit.max_count, count, amount)
        if limit.max_amount is not None and total_amount > limit.max_amount:
            self._deny(label, "amount", limit.max_amount, total_amount, amount)

    def _breaker_open(self, action: str) -> bool:
        window_id = self._window(self._config.breaker_window_seconds)
        return self._breaker_windows.get(action) == window_id

    def _deny(self, scope: str, dimension: str, limit: int, current: int, amount: int) -> None:
        message = f"risk limit exceeded: {scope} {dimension} {current}/{limit}"
        if self._config.mode == "monitor":
            logger.warning(message, extra={"scope": scope, "amount": amount})
            return
        raise GatewayApiError(
            "RISK_LIMIT",
            message,
            http_status=429,
            details={"scope": scope, "dimension": dimension, "limit": limit, "current": current, "amount": amount},
        )

    def check(
        self,
        action: str,
        *,
        account_id: str | None,
        client_ip: str | None,
        amount: int | None = None,
    ) -> None:
        if self._config.mode == "off":
            return
        if self._config.global_paused:
            self._deny("global_pause", "count", 0, 1, amount or 0)
        if self._breaker_open(action):
            self._deny("circuit_breaker", "count", 0, 1, amount or 0)

        normalized_amount = int(amount or 0)
        self._check_limit("global", f"global:{action}", self._config.global_limit, normalized_amount)

        if account_id:
            self._check_limit(
                "account",
                f"account:{account_id}:{action}",
                self._config.account_limit,
                normalized_amount,
            )

        if client_ip:
            self._check_limit(
                "ip",
                f"ip:{client_ip}:{action}",
                self._config.ip_limit,
                normalized_amount,
            )

        action_limit = self._config.action_limits.get(action)
        if action_limit:
            self._check_limit(f"action:{action}", f"action:{action}", action_limit, normalized_amount)

    def record_failure(self, action: str) -> None:
        if self._config.breaker_errors_per_min <= 0:
            return
        window_id = self._window(self._config.breaker_window_seconds)
        count, stored_window = self._error_counters.get(action, (0, window_id))
        if stored_window != window_id:
            count = 0
        count += 1
        self._error_counters[action] = (count, window_id)
        if count >= self._config.breaker_errors_per_min:
            self._breaker_windows[action] = window_id
            logger.warning("circuit breaker opened", extra={"action": action, "count": count})
