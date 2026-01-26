from __future__ import annotations

from dataclasses import dataclass
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile


class EvidenceError(ValueError):
    pass


_MAX_PAYLOAD_DEPTH = 6
_MAX_PAYLOAD_ITEMS = 64
_MAX_TEXT_LEN = 256

ALLOWED_ARTIFACT_NAMES = {
    "protocol_anchor.json",
    "inputs.json",
    "outputs.json",
    "receipt_hashes.json",
    "state_hash.txt",
    "replay_ok.txt",
    "stdout.txt",
    "evidence.json",
    "manifest.json",
    "export.zip",
}


@dataclass(frozen=True)
class EvidencePayload:
    protocol_anchor: dict[str, object]
    inputs: dict[str, object]
    outputs: dict[str, object]
    receipt_hashes: list[str]
    state_hash: str
    replay_ok: bool
    stdout: str


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    status: str
    error: str | None


def _repo_root() -> Path:
    path = Path(__file__).resolve()
    for _ in range(5):
        path = path.parent
    return path


def _ensure_paths() -> None:
    repo_root = _repo_root()
    paths = [
        repo_root / "packages" / "e2e-private-transfer" / "src",
        repo_root / "packages" / "l2-private-ledger" / "src",
        repo_root / "packages" / "l0-zk-id" / "src",
        repo_root / "packages" / "l2-economics" / "src",
        repo_root / "packages" / "l2-platform-fee" / "src",
        repo_root / "packages" / "l1-chain" / "src",
        repo_root / "packages" / "wallet-kernel" / "src",
    ]
    for path in paths:
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


def _json_dumps(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _sanitize_run_id(run_id: str) -> str:
    if not run_id:
        raise EvidenceError("run_id required")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", run_id):
        raise EvidenceError("run_id contains invalid characters")
    return run_id


def _run_key(run_id: str) -> str:
    rid = _sanitize_run_id(run_id)
    digest = hashlib.sha256(rid.encode("utf-8")).hexdigest()
    return digest[:32]


def _validate_artifact_name(name: str) -> str:
    if not name:
        raise EvidenceError("artifact name required")
    if "/" in name or "\\" in name:
        raise EvidenceError("artifact name must be basename")
    if name not in ALLOWED_ARTIFACT_NAMES:
        raise EvidenceError("artifact name not allowed")
    return name


def _safe_run_dir(run_root: Path, run_id: str) -> Path:
    key = _run_key(run_id)
    run_dir = (run_root / key).resolve()
    root_resolved = run_root.resolve()
    if root_resolved not in run_dir.parents and run_dir != root_resolved:
        raise EvidenceError("run_id not allowed")
    return run_dir


def _safe_artifact_path(run_root: Path, run_id: str, name: str) -> Path:
    run_dir = _safe_run_dir(run_root, run_id)
    safe_name = _validate_artifact_name(name)
    target = (run_dir / "artifacts" / safe_name).resolve()
    if run_dir not in target.parents:
        raise EvidenceError("artifact path not allowed")
    return target


def _run_root(base_dir: Path | None = None) -> Path:
    if base_dir is not None:
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir
    root = _repo_root() / "apps" / "nyx-backend" / "runs"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _protocol_anchor() -> dict[str, str]:
    commit = _run_git(["rev-parse", "HEAD"])
    describe = _run_git(["describe", "--tags", "--always"])
    tags_raw = _run_git(["tag", "--points-at", "HEAD"])
    tags = sorted([t for t in tags_raw.splitlines() if t.strip()])
    tag = tags[0] if tags else ""
    return {"tag": tag, "commit": commit, "describe": describe}


def _validate_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value or isinstance(value, bool):
        raise EvidenceError(f"{name} required")
    if not re.fullmatch(r"[A-Za-z0-9_./-]{1,64}", value):
        raise EvidenceError(f"{name} contains invalid characters")
    return value


def _validate_payload(payload: object, depth: int = 0) -> object:
    if depth > _MAX_PAYLOAD_DEPTH:
        raise EvidenceError("payload too deep")
    if payload is None:
        return None
    if isinstance(payload, (str, int)) and not isinstance(payload, bool):
        if isinstance(payload, str) and len(payload) > _MAX_TEXT_LEN:
            raise EvidenceError("payload text too long")
        return payload
    if isinstance(payload, bool):
        return payload
    if isinstance(payload, list):
        if len(payload) > _MAX_PAYLOAD_ITEMS:
            raise EvidenceError("payload list too large")
        return [_validate_payload(item, depth + 1) for item in payload]
    if isinstance(payload, dict):
        if len(payload) > _MAX_PAYLOAD_ITEMS:
            raise EvidenceError("payload map too large")
        out = {}
        for key, value in payload.items():
            if not isinstance(key, str):
                raise EvidenceError("payload keys must be text")
            if len(key) > _MAX_TEXT_LEN:
                raise EvidenceError("payload key too long")
            out[key] = _validate_payload(value, depth + 1)
        return out
    raise EvidenceError("payload type not allowed")


def _summary_stdout(state_hash: str, receipt_hashes: list[str], replay_ok: bool) -> str:
    receipt_prefix = receipt_hashes[0][:12] if receipt_hashes else ""
    return (
        "state_hash="
        f"{state_hash[:12]} "
        "receipt_hash="
        f"{receipt_prefix} "
        "replay_ok="
        f"{replay_ok}"
    )


def _platform_fee_for_marketplace(payload: object) -> dict[str, object]:
    from action import ActionDescriptor, ActionKind
    from engine import FeeEngineV0
    from l2_platform_fee.fee_hook import enforce_platform_fee, quote_platform_fee

    action = ActionDescriptor(
        kind=ActionKind.STATE_MUTATION,
        module="marketplace",
        action="order_intent",
        payload=payload,
    )
    engine = FeeEngineV0()
    payer = "platform-payer"
    platform_amount = _platform_fee_amount(payload)
    quote = quote_platform_fee(
        engine,
        action,
        payer=payer,
        platform_fee_amount=platform_amount,
    )
    receipt = enforce_platform_fee(
        engine,
        quote,
        paid_protocol_vector=quote.protocol_quote.fee_vector,
        paid_platform_amount=quote.platform_fee_amount,
        payer=quote.payer,
    )
    return {
        "platform_fee_amount": quote.platform_fee_amount,
        "protocol_fee_total": quote.protocol_quote.fee_vector.total(),
        "total_due": quote.total_due,
        "total_paid": receipt.total_paid,
        "payer": quote.payer,
        "treasury_address": _treasury_address(),
    }


def _treasury_address() -> str:
    address = os.environ.get("NYX_TESTNET_TREASURY_ADDRESS", "").strip()
    if not address:
        address = os.environ.get("NYX_TESTNET_FEE_ADDRESS", "").strip()
    if not address:
        return "testnet-treasury-unconfigured"
    return address


def _platform_fee_amount(payload: object) -> int:
    raw = os.environ.get("NYX_PLATFORM_FEE_BPS", "").strip()
    if not raw:
        return 1
    try:
        bps = int(raw)
    except ValueError as exc:
        raise EvidenceError("NYX_PLATFORM_FEE_BPS must be int") from exc
    if bps < 0 or bps > 10_000:
        raise EvidenceError("NYX_PLATFORM_FEE_BPS out of bounds")
    if bps == 0:
        return 0
    base = 1
    if isinstance(payload, dict):
        for key in ("amount", "price", "qty"):
            value = payload.get(key)
            if isinstance(value, int) and not isinstance(value, bool) and value > 0:
                base = value
                break
    amount = (base * bps) // 10_000
    return amount if amount > 0 else 1


def _fee_summary(module: str, action: str, payload: object) -> dict[str, object]:
    from action import ActionDescriptor, ActionKind
    from engine import FeeEngineV0
    from l2_platform_fee.fee_hook import enforce_platform_fee, quote_platform_fee

    platform_amount = _platform_fee_amount(payload)
    payer = "testnet-payer"
    if isinstance(payload, dict):
        candidate = payload.get("from_address")
        if isinstance(candidate, str) and candidate:
            payer = candidate
    descriptor = ActionDescriptor(
        kind=ActionKind.STATE_MUTATION,
        module=module,
        action=action,
        payload=payload,
    )
    engine = FeeEngineV0()
    quote = quote_platform_fee(engine, descriptor, payer=payer, platform_fee_amount=platform_amount)
    receipt = enforce_platform_fee(
        engine,
        quote,
        paid_protocol_vector=quote.protocol_quote.fee_vector,
        paid_platform_amount=quote.platform_fee_amount,
        payer=quote.payer,
    )
    return {
        "fee_total": receipt.total_paid,
        "fee_breakdown": {
            "protocol_fee_total": quote.protocol_quote.fee_vector.total(),
            "platform_fee_amount": quote.platform_fee_amount,
        },
        "payer": quote.payer,
        "treasury_address": _treasury_address(),
    }


def _entertainment_state(seed: int, payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise EvidenceError("entertainment payload must be object")
    mode = payload.get("mode")
    step = payload.get("step")
    if not isinstance(mode, str) or not mode or isinstance(mode, bool):
        raise EvidenceError("mode required")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", mode):
        raise EvidenceError("mode contains invalid characters")
    if not isinstance(step, int) or isinstance(step, bool):
        raise EvidenceError("step must be int")
    if step < 0 or step > 10:
        raise EvidenceError("step out of bounds")
    digest = hashlib.sha256(
        f"NYX:ENT:STEP:v1:{mode}:{step}:{seed}".encode("utf-8")
    ).hexdigest()
    return {"mode": mode, "step": step, "state_hash": digest}


def run_evidence(
    seed: int,
    run_id: str,
    module: str,
    action: str,
    payload: object | None = None,
    base_dir: Path | None = None,
) -> EvidencePayload:
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise EvidenceError("seed must be int")
    if not isinstance(run_id, str) or isinstance(run_id, bool):
        raise EvidenceError("run_id required")
    mod = _validate_text(module, "module")
    act = _validate_text(action, "action")
    payload = _validate_payload(payload)

    _ensure_paths()
    from e2e_private_transfer.pipeline import run_private_transfer
    from e2e_private_transfer.replay import replay_and_verify

    rid = _sanitize_run_id(run_id)
    run_root = _run_root(base_dir)
    run_dir = _safe_run_dir(run_root, rid)
    artifacts_dir = run_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_id.txt").write_text(rid + "\n", encoding="utf-8")

    trace, _ = run_private_transfer(seed=seed)
    replay_ok = replay_and_verify(trace)
    if not replay_ok:
        raise EvidenceError("replay verification failed")

    protocol_anchor = _protocol_anchor()
    inputs = {"seed": seed, "module": mod, "action": act, "payload": payload}
    receipt_hashes = [
        trace.fee.receipt_hash_hex,
        trace.chain.tx_hash_hex,
        trace.chain.block_hash_hex,
    ]
    outputs = {
        "state_hash": trace.chain.state_root_after_hex,
        "receipt_hashes": receipt_hashes,
        "replay_ok": replay_ok,
    }
    if (mod, act) in {
        ("exchange", "route_swap"),
        ("exchange", "place_order"),
        ("exchange", "cancel_order"),
        ("marketplace", "order_intent"),
        ("marketplace", "listing_publish"),
        ("marketplace", "purchase_listing"),
        ("wallet", "transfer"),
    }:
        outputs.update(_fee_summary(mod, act, payload))
    if mod == "marketplace" and act == "order_intent":
        outputs["platform_fee"] = _platform_fee_for_marketplace(payload)
    if mod == "entertainment" and act == "state_step":
        outputs["entertainment_state"] = _entertainment_state(seed, payload)

    (artifacts_dir / "protocol_anchor.json").write_text(_json_dumps(protocol_anchor), encoding="utf-8")
    (artifacts_dir / "inputs.json").write_text(_json_dumps(inputs), encoding="utf-8")
    (artifacts_dir / "outputs.json").write_text(_json_dumps(outputs), encoding="utf-8")
    (artifacts_dir / "receipt_hashes.json").write_text(_json_dumps(receipt_hashes), encoding="utf-8")
    (artifacts_dir / "state_hash.txt").write_text(outputs["state_hash"] + "\n", encoding="utf-8")
    (artifacts_dir / "replay_ok.txt").write_text(("true" if replay_ok else "false") + "\n", encoding="utf-8")

    stdout_text = _summary_stdout(outputs["state_hash"], receipt_hashes, replay_ok)
    (artifacts_dir / "stdout.txt").write_text(stdout_text, encoding="utf-8")

    evidence_payload = {
        "protocol_anchor": protocol_anchor,
        "inputs": inputs,
        "outputs": outputs,
        "receipt_hashes": receipt_hashes,
        "state_hash": outputs["state_hash"],
        "replay_ok": replay_ok,
        "stdout": stdout_text,
    }
    (run_dir / "evidence.json").write_text(_json_dumps(evidence_payload), encoding="utf-8")

    return EvidencePayload(
        protocol_anchor=protocol_anchor,
        inputs=inputs,
        outputs=outputs,
        receipt_hashes=receipt_hashes,
        state_hash=outputs["state_hash"],
        replay_ok=replay_ok,
        stdout=stdout_text,
    )


def load_evidence(run_id: str, base_dir: Path | None = None) -> EvidencePayload:
    rid = _sanitize_run_id(run_id)
    run_root = _run_root(base_dir)
    run_dir = _safe_run_dir(run_root, rid)
    artifacts_dir = run_dir / "artifacts"
    if not artifacts_dir.exists():
        raise EvidenceError("run_id not found")

    protocol_anchor = _read_json(artifacts_dir / "protocol_anchor.json")
    inputs = _read_json(artifacts_dir / "inputs.json")
    outputs = _read_json(artifacts_dir / "outputs.json")
    receipt_hashes = _read_json(artifacts_dir / "receipt_hashes.json")
    state_hash = (artifacts_dir / "state_hash.txt").read_text(encoding="utf-8").strip()
    replay_ok_text = (artifacts_dir / "replay_ok.txt").read_text(encoding="utf-8").strip()
    stdout = (artifacts_dir / "stdout.txt").read_text(encoding="utf-8")

    replay_ok = replay_ok_text == "true"
    if not isinstance(receipt_hashes, list):
        raise EvidenceError("receipt_hashes must be list")

    return EvidencePayload(
        protocol_anchor=protocol_anchor,
        inputs=inputs,
        outputs=outputs,
        receipt_hashes=receipt_hashes,
        state_hash=state_hash,
        replay_ok=replay_ok,
        stdout=stdout,
    )


def verify_evidence_payload(payload: EvidencePayload) -> None:
    if not isinstance(payload.outputs, dict):
        raise EvidenceError("outputs must be dict")
    outputs_state = payload.outputs.get("state_hash")
    if outputs_state != payload.state_hash:
        raise EvidenceError("state_hash mismatch")
    outputs_receipts = payload.outputs.get("receipt_hashes")
    if outputs_receipts != payload.receipt_hashes:
        raise EvidenceError("receipt_hashes mismatch")
    outputs_replay = payload.outputs.get("replay_ok")
    if outputs_replay != payload.replay_ok:
        raise EvidenceError("replay_ok mismatch")


def list_runs(base_dir: Path | None = None) -> list[RunRecord]:
    run_root = _run_root(base_dir)
    if not run_root.exists():
        return []
    records: list[RunRecord] = []
    for entry in sorted(run_root.iterdir()):
        if not entry.is_dir():
            continue
        status = "complete" if (entry / "artifacts").exists() else "unknown"
        run_id_path = entry / "run_id.txt"
        run_id = entry.name
        if run_id_path.exists():
            run_id = run_id_path.read_text(encoding="utf-8").strip() or entry.name
        records.append(RunRecord(run_id=run_id, status=status, error=None))
    return records


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_export_zip(run_id: str, base_dir: Path | None = None) -> bytes:
    rid = _sanitize_run_id(run_id)
    run_root = _run_root(base_dir)
    run_dir = _safe_run_dir(run_root, rid)
    artifacts_dir = run_dir / "artifacts"
    if not artifacts_dir.exists():
        raise EvidenceError("run_id not found")

    files = [
        Path("evidence.json"),
        Path("artifacts") / "protocol_anchor.json",
        Path("artifacts") / "inputs.json",
        Path("artifacts") / "outputs.json",
        Path("artifacts") / "receipt_hashes.json",
        Path("artifacts") / "state_hash.txt",
        Path("artifacts") / "replay_ok.txt",
        Path("artifacts") / "stdout.txt",
    ]

    manifest_entries = []
    payloads: list[tuple[str, bytes]] = []
    for rel in files:
        full_path = run_dir / rel
        content = full_path.read_bytes()
        payloads.append((str(rel), content))
        manifest_entries.append({"path": str(rel), "sha256": _sha256_bytes(content)})

    manifest = _json_dumps({"files": sorted(manifest_entries, key=lambda x: x["path"])})
    payloads.append(("manifest.json", manifest.encode("utf-8")))

    payloads_sorted = sorted(payloads, key=lambda item: item[0])
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_STORED) as zip_file:
        for name, content in payloads_sorted:
            info = zipfile.ZipInfo(name)
            info.date_time = (1980, 1, 1, 0, 0, 0)
            zip_file.writestr(info, content)
    return buffer.getvalue()


__all__ = [
    "EvidenceError",
    "EvidencePayload",
    "RunRecord",
    "build_export_zip",
    "list_runs",
    "load_evidence",
    "run_evidence",
]
