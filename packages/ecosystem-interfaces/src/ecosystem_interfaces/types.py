from __future__ import annotations

from dataclasses import dataclass


class InterfaceError(ValueError):
    pass


def require_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise InterfaceError(f"{name} must be non-empty string")
    return value


@dataclass(frozen=True)
class ModuleId:
    value: str

    def __post_init__(self) -> None:
        require_text(self.value, "module_id")


@dataclass(frozen=True)
class RequestId:
    value: str

    def __post_init__(self) -> None:
        require_text(self.value, "request_id")


@dataclass(frozen=True)
class EvidenceRef:
    bundle_id: str

    def __post_init__(self) -> None:
        require_text(self.bundle_id, "bundle_id")
