from __future__ import annotations

from e2e_private_transfer.hashing import compare_digest, hex_to_bytes32
from e2e_private_transfer.trace import TransferTrace

from l2_private_ledger.actions import ActionKind, LedgerAction, PrivateMint, PrivateSpend
from l2_private_ledger.fee_binding import compute_action_hash, quote_fee_for_private_action
from l2_private_ledger.proof_wiring import (
    DEFAULT_CONTEXT_ID,
    DEFAULT_STATEMENT_ID,
    verify_private_action,
)

from action import ActionDescriptor, ActionKind as FeeActionKind
from engine import FeeEngineV0
from fee import FeeComponentId, FeeVector
from quote import FeePayment, create_quote, create_receipt

from l1_chain.devnet.adapter import DeterministicInMemoryChainAdapter
from l1_chain.types import ChainAccount, ChainId, StateProof, StateRoot, TxSignature, build_tx_envelope


class ReplayError(ValueError):
    pass


def replay_and_verify(trace: TransferTrace) -> bool:
    try:
        action = _action_from_trace(trace)
        ledger_root = hex_to_bytes32(trace.action.ledger_root_hex, "ledger_root")
        action_hash = hex_to_bytes32(trace.action.action_hash_hex, "action_hash")
        expected_hash = compute_action_hash(action)
        if not compare_digest(action_hash, expected_hash):
            return False

        envelope = trace.proof.to_envelope()
        if not verify_private_action(
            envelope,
            ledger_root,
            action,
            context_id=DEFAULT_CONTEXT_ID,
            statement_id=DEFAULT_STATEMENT_ID,
        ):
            return False
        if not trace.sanity.wrong_context_failed:
            return False

        fee_vector = _fee_vector_from_components(trace)
        if fee_vector.total() != trace.fee.total:
            return False
        if fee_vector.total() <= 0:
            return False

        descriptor_hash = _fee_descriptor_action_hash(trace, action_hash)
        quote = create_quote(descriptor_hash, fee_vector, trace.fee.payer)
        if not compare_digest(quote.quote_hash, hex_to_bytes32(trace.fee.quote_hash_hex, "quote_hash")):
            return False

        payment = FeePayment(
            payer=trace.fee.payer,
            quote_hash=quote.quote_hash,
            paid_vector=fee_vector,
        )
        receipt = create_receipt(quote, payment)
        if not compare_digest(receipt.receipt_hash, hex_to_bytes32(trace.fee.receipt_hash_hex, "receipt_hash")):
            return False

        engine = FeeEngineV0()
        compare_quote = quote_fee_for_private_action(
            engine,
            action,
            ledger_root,
            action_hash,
            payer=trace.fee.payer,
        )
        compare_quote_b = quote_fee_for_private_action(
            engine,
            action,
            ledger_root,
            action_hash,
            payer="payer-b",
        )
        sponsor_same = compare_quote.fee_vector == compare_quote_b.fee_vector
        if sponsor_same != trace.fee.sponsor_same_amount:
            return False

        chain_id = ChainId(trace.chain.chain_id)
        sender = ChainAccount(trace.chain.sender)
        nonce = bytes.fromhex(trace.chain.nonce_hex)
        payload = bytes.fromhex(trace.chain.payload_hex)
        signature = TxSignature(bytes.fromhex(trace.chain.signature_hex))
        tx = build_tx_envelope(
            chain_id=chain_id,
            sender=sender,
            nonce=nonce,
            payload=payload,
            signature=signature,
        )
        if not compare_digest(tx.tx_hash.value, hex_to_bytes32(trace.chain.tx_hash_hex, "tx_hash")):
            return False

        adapter = DeterministicInMemoryChainAdapter(chain_id)
        pre_root = adapter.read_state(b"")[1].value
        if not compare_digest(pre_root, hex_to_bytes32(trace.chain.state_root_before_hex, "state_root_before")):
            return False

        tx_hash = adapter.submit_tx(tx)
        block_ref = adapter.mine_block()
        if block_ref.height != trace.chain.block_height:
            return False
        if not compare_digest(block_ref.block_hash, hex_to_bytes32(trace.chain.block_hash_hex, "block_hash")):
            return False

        post_root = adapter.read_state(b"")[1].value
        if not compare_digest(post_root, hex_to_bytes32(trace.chain.state_root_after_hex, "state_root_after")):
            return False

        finality = adapter.get_finality(tx_hash)
        if finality is None:
            return False
        if not compare_digest(finality.proof_bytes, bytes.fromhex(trace.chain.finality_proof_hex)):
            return False

        key_bytes = bytes.fromhex(trace.chain.state_proof.key_hex)
        value_hex = trace.chain.state_proof.value_hex
        value_bytes = None if value_hex is None else bytes.fromhex(value_hex)
        state_root = StateRoot(hex_to_bytes32(trace.chain.state_proof.state_root_hex, "state_root"))
        proof_bytes = bytes.fromhex(trace.chain.state_proof.proof_bytes_hex)
        proof = StateProof(
            chain_id=chain_id,
            key=key_bytes,
            value=value_bytes,
            state_root=state_root,
            proof_bytes=proof_bytes,
        )
        if not adapter.verify_state_proof(proof):
            return False
        built_proof = adapter.build_state_proof(key_bytes)
        if not compare_digest(built_proof.proof_bytes, proof.proof_bytes):
            return False
        if not compare_digest(built_proof.state_root.value, proof.state_root.value):
            return False
        if (built_proof.value is None) != (proof.value is None):
            return False
        if built_proof.value is not None:
            if not compare_digest(built_proof.value, proof.value):
                return False

        return True
    except Exception:
        return False


def _action_from_trace(trace: TransferTrace) -> LedgerAction:
    if trace.action.kind == ActionKind.PRIVATE_MINT.value:
        payload = trace.action.payload
        if "commitment" not in payload:
            raise ReplayError("payload missing commitment")
        commitment = hex_to_bytes32(payload["commitment"], "commitment")
        return LedgerAction(ActionKind.PRIVATE_MINT, PrivateMint(commitment))
    if trace.action.kind == ActionKind.PRIVATE_SPEND.value:
        payload = trace.action.payload
        if "nullifier" not in payload:
            raise ReplayError("payload missing nullifier")
        nullifier = hex_to_bytes32(payload["nullifier"], "nullifier")
        return LedgerAction(ActionKind.PRIVATE_SPEND, PrivateSpend(nullifier))
    raise ReplayError("unsupported action kind")


def _fee_vector_from_components(trace: TransferTrace) -> FeeVector:
    components = []
    for entry in trace.fee.components:
        if not isinstance(entry, dict):
            raise ReplayError("component entry invalid")
        component_id = entry.get("component")
        amount = entry.get("amount")
        if not isinstance(component_id, str):
            raise ReplayError("component id invalid")
        components.append((FeeComponentId(component_id), amount))
    return FeeVector(tuple(components))


def _fee_descriptor_action_hash(trace: TransferTrace, action_hash: bytes) -> bytes:
    payload = {
        "ledger_root": trace.action.ledger_root_hex,
        "action_hash": action_hash.hex(),
        "action_kind": trace.action.kind,
        "payload": trace.action.payload,
    }
    descriptor = ActionDescriptor(
        kind=FeeActionKind.STATE_MUTATION,
        module="l2.private_ledger",
        action=trace.action.kind,
        payload=payload,
        metadata=None,
    )
    return descriptor.action_hash()
