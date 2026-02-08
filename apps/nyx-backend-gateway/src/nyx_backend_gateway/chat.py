from __future__ import annotations

from nyx_backend_gateway.errors import GatewayError
from nyx_backend_gateway.identifiers import deterministic_id
from nyx_backend_gateway.storage import MessageEvent, insert_message_event
from nyx_backend_gateway.validation import validate_chat_payload


def record_message_event(conn, run_id: str, payload: dict[str, object], caller_account_id: str | None) -> None:
    if not caller_account_id:
        raise GatewayError("auth required")
    validated = validate_chat_payload(payload)
    insert_message_event(
        conn,
        MessageEvent(
            message_id=deterministic_id("message", run_id),
            channel=validated["channel"],
            sender_account_id=caller_account_id,
            body=validated["message"],
            run_id=run_id,
        ),
    )
