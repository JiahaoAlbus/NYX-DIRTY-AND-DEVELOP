from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .types import EvidenceRef, ModuleId, RequestId, require_text


@dataclass(frozen=True)
class ModuleContext:
    module_id: ModuleId


class MarketplaceModule(Protocol):
    def create_listing(self, request_id: RequestId, context: ModuleContext) -> EvidenceRef:
        raise NotImplementedError

    def update_listing(self, request_id: RequestId, context: ModuleContext) -> EvidenceRef:
        raise NotImplementedError


class ChatModule(Protocol):
    def post_message(self, request_id: RequestId, context: ModuleContext) -> EvidenceRef:
        raise NotImplementedError


class EntertainmentModule(Protocol):
    def submit_action(self, request_id: RequestId, context: ModuleContext) -> EvidenceRef:
        raise NotImplementedError


def validate_context_label(label: str) -> str:
    return require_text(label, "context_label")
