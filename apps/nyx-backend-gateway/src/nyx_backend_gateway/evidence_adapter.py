from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any

from nyx_backend_gateway.errors import GatewayError
from nyx_backend_gateway.identifiers import receipt_id
from nyx_backend_gateway.paths import backend_src, run_root
from nyx_backend_gateway.storage import EvidenceRun, Receipt, insert_evidence_run, insert_receipt


@dataclass(frozen=True)
class EvidenceOutcome:
    state_hash: str
    receipt_hashes: list[str]
    replay_ok: bool


def _ensure_backend_import() -> None:
    path = str(backend_src())
    if path not in sys.path:
        sys.path.insert(0, path)


def run_and_record(
    *,
    seed: int,
    run_id: str,
    module: str,
    action: str,
    payload: dict[str, Any],
    conn,
    base_dir=None,
) -> EvidenceOutcome:
    _ensure_backend_import()
    from nyx_backend.evidence import EvidenceError, run_evidence

    base_dir = base_dir or run_root()
    try:
        evidence = run_evidence(
            seed=seed,
            run_id=run_id,
            module=module,
            action=action,
            payload=payload,
            base_dir=base_dir,
        )
    except EvidenceError as exc:
        raise GatewayError(str(exc)) from exc

    insert_evidence_run(
        conn,
        EvidenceRun(
            run_id=run_id,
            module=module,
            action=action,
            seed=seed,
            state_hash=evidence.state_hash,
            receipt_hashes=evidence.receipt_hashes,
            replay_ok=evidence.replay_ok,
        ),
    )
    insert_receipt(
        conn,
        Receipt(
            receipt_id=receipt_id(run_id),
            module=module,
            action=action,
            state_hash=evidence.state_hash,
            receipt_hashes=evidence.receipt_hashes,
            replay_ok=evidence.replay_ok,
            run_id=run_id,
        ),
    )

    return EvidenceOutcome(
        state_hash=evidence.state_hash,
        receipt_hashes=evidence.receipt_hashes,
        replay_ok=evidence.replay_ok,
    )
