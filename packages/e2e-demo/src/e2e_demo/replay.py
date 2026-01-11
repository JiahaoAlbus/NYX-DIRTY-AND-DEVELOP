from __future__ import annotations

from dataclasses import dataclass

from action import ActionDescriptor, ActionKind
from engine import FeeEngineV0
from fee import FeeComponentId, FeeVector
from quote import FeePayment
from verifier import MockProofAdapter, verify

from l1_chain.devnet.adapter import DeterministicInMemoryChainAdapter
from l1_chain.types import (
    ChainAccount,
    ChainId,
    FinalityProof,
    StateProof,
    StateRoot,
    TxEnvelope,
    TxHash,
    TxSignature,
)

from e2e_demo.hashing import compare_digest, hex_to_bytes32
from e2e_demo.trace import E2ETrace


@dataclass(frozen=True)
class ReplayResult:
    ok: bool
    errors: tuple[str, ...]


def _component_pairs(components: list[dict[str, object]]) -> tuple[tuple[FeeComponentId, int], ...]:
    pairs: list[tuple[FeeComponentId, int]] = []
    for entry in components:
        component = FeeComponentId(entry["component"])
        amount = entry["amount"]
        if not isinstance(amount, int) or isinstance(amount, bool):
            raise ValueError("fee component amount invalid")
        pairs.append((component, amount))
    return tuple(pairs)


def replay_and_verify(trace: E2ETrace) -> ReplayResult:
    errors: list[str] = []

    try:
        envelope = trace.proof.to_envelope()
    except Exception:
        errors.append("proof envelope invalid")
        return ReplayResult(ok=False, errors=tuple(errors))

    adapter = MockProofAdapter()
    if not verify(
        envelope,
        hex_to_bytes32(trace.proof.context_id_hex, "context_id"),
        trace.proof.statement_id,
        adapter,
    ):
        errors.append("proof verify failed")

    if verify(
        envelope,
        hex_to_bytes32(trace.proof.context_id_hex, "context_id"),
        trace.proof.statement_id,
        adapter,
    ) is False and trace.sanity.correct_context_verified:
        errors.append("sanity mismatch: expected correct context")

    if trace.sanity.wrong_context_verified:
        errors.append("sanity mismatch: wrong context verified")

    if trace.identity.commitment_hex != trace.proof.public_inputs.get("identity_commitment"):
        errors.append("identity commitment mismatch")

    try:
        action_kind = ActionKind(trace.action.kind)
        action_descriptor = ActionDescriptor(
            kind=action_kind,
            module=trace.action.module,
            action=trace.action.action,
            payload=trace.action.payload,
            metadata=trace.action.metadata,
        )
    except Exception:
        errors.append("action descriptor invalid")
        action_descriptor = None

    if action_descriptor is not None:
        if trace.action.action_hash_hex != action_descriptor.action_hash().hex():
            errors.append("action hash mismatch")
        fee_engine = FeeEngineV0()
        try:
            quote = fee_engine.quote(action_descriptor, trace.fee.payer)
            if quote.fee_vector.total() <= 0:
                errors.append("fee total not positive")
            if quote.fee_vector.total() != trace.fee.total:
                errors.append("fee total mismatch")
            if quote.fee_vector.canonical_obj() != trace.fee.components:
                errors.append("fee components mismatch")
            if not compare_digest(quote.quote_hash, hex_to_bytes32(trace.fee.quote_hash_hex, "quote_hash")):
                errors.append("quote hash mismatch")
            payment = FeePayment(
                payer=trace.fee.payer,
                quote_hash=quote.quote_hash,
                paid_vector=quote.fee_vector,
            )
            receipt = fee_engine.enforce(quote, payment)
            if not compare_digest(receipt.receipt_hash, hex_to_bytes32(trace.fee.receipt_hash_hex, "receipt_hash")):
                errors.append("receipt hash mismatch")
        except Exception:
            errors.append("fee replay failed")

    try:
        chain = DeterministicInMemoryChainAdapter(ChainId(trace.chain.chain_id))
        tx = TxEnvelope(
            chain_id=ChainId(trace.chain.chain_id),
            sender=ChainAccount(trace.chain.sender),
            nonce=hex_to_bytes32(trace.chain.nonce_hex, "nonce"),
            payload=bytes.fromhex(trace.chain.payload_hex),
            signature=TxSignature(bytes.fromhex(trace.chain.signature_hex)),
            tx_hash=TxHash(hex_to_bytes32(trace.chain.tx_hash_hex, "tx_hash")),
        )
        pre_root = chain.read_state(b"")[1].value
        chain.submit_tx(tx)
        block_ref = chain.mine_block()
        post_root = chain.read_state(b"")[1].value
        if not compare_digest(pre_root, hex_to_bytes32(trace.chain.state_root_before_hex, "state_root_before")):
            errors.append("state root before mismatch")
        if not compare_digest(post_root, hex_to_bytes32(trace.chain.state_root_after_hex, "state_root_after")):
            errors.append("state root after mismatch")
        if block_ref.height != trace.chain.block_height:
            errors.append("block height mismatch")
        if not compare_digest(block_ref.block_hash, hex_to_bytes32(trace.chain.block_hash_hex, "block_hash")):
            errors.append("block hash mismatch")
        finality = chain.get_finality(tx.tx_hash)
        if finality is None:
            errors.append("finality missing")
        else:
            if not isinstance(finality, FinalityProof):
                errors.append("finality type mismatch")
            if not compare_digest(finality.proof_bytes, bytes.fromhex(trace.chain.finality_proof_hex)):
                errors.append("finality proof mismatch")
        state_proof = StateProof(
            chain_id=ChainId(trace.chain.chain_id),
            key=bytes.fromhex(trace.chain.state_proof.key_hex),
            value=(
                None
                if trace.chain.state_proof.value_hex is None
                else bytes.fromhex(trace.chain.state_proof.value_hex)
            ),
            state_root=StateRoot(hex_to_bytes32(trace.chain.state_proof.state_root_hex, "state_root")),
            proof_bytes=bytes.fromhex(trace.chain.state_proof.proof_bytes_hex),
        )
        if not chain.verify_state_proof(state_proof):
            errors.append("state proof verify failed")
    except Exception:
        errors.append("chain replay failed")

    return ReplayResult(ok=len(errors) == 0, errors=tuple(errors))
