from __future__ import annotations


class GatewayError(ValueError):
    pass


class GatewayApiError(GatewayError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        http_status: int = 400,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.http_status = http_status
        self.details = details or {}
