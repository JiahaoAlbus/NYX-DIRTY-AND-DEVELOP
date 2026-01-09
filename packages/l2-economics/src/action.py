from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from canonical import CanonicalizationError, canonicalize, require_text
from hashing import encode_len_prefixed, encode_len_prefixed_bytes, sha256


class ActionKind(Enum):
    READ_ONLY = "read_only"
    STATE_MUTATION = "state_mutation"


class ActionError(ValueError):
    pass


@dataclass(frozen=True)
class ActionDescriptor:
    kind: ActionKind
    module: str
    action: str
    payload: object
    metadata: dict | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ActionKind):
            raise ActionError("kind must be ActionKind")
        try:
            require_text(self.module, "module")
            require_text(self.action, "action")
        except CanonicalizationError as exc:
            raise ActionError(str(exc)) from exc
        self._validate_payload(self.payload)
        if self.metadata is not None:
            if not isinstance(self.metadata, dict):
                raise ActionError("metadata must be a dict")
            self._validate_payload(self.metadata)

    def canonical_bytes(self) -> bytes:
        payload = {
            "kind": self.kind.value,
            "module": self.module,
            "action": self.action,
            "payload": self.payload,
            "metadata": self.metadata,
        }
        return canonicalize(payload)

    def framed_preimage(self) -> bytes:
        payload_bytes = canonicalize(self.payload)
        metadata_bytes = (
            canonicalize(self.metadata) if self.metadata is not None else canonicalize(None)
        )
        return b"".join(
            [
                encode_len_prefixed(self.kind.value, "kind"),
                encode_len_prefixed(self.module, "module"),
                encode_len_prefixed(self.action, "action"),
                encode_len_prefixed_bytes(payload_bytes, "payload"),
                encode_len_prefixed_bytes(metadata_bytes, "metadata"),
            ]
        )

    def action_hash(self) -> bytes:
        return sha256(self.framed_preimage())

    @staticmethod
    def _validate_payload(value: object) -> None:
        try:
            canonicalize(value)
        except CanonicalizationError as exc:
            raise ActionError(str(exc)) from exc
