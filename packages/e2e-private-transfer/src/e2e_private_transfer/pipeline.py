from __future__ import annotations

from dataclasses import dataclass

from e2e_private_transfer.hashing import compare_digest, sha256
from e2e_private_transfer.trace import (
    ChainTrace,
    FeeTrace,
    IdentityTrace,
    PrivateActionTrace,
    ProofEnvelopeTrace,
    SanityTrace,
    StateProofTrace,
    TransferTrace,
)

from l2_private_ledger.actions import ActionKind, LedgerAction, PrivateMint
from l2_private_ledger.fee_binding import (
    compute_action_hash,
    enforce_fee_for_private_action,
    quote_fee_for_private_action,
)
from l2_private_ledger.kernel import apply_action
from l2_private_ledger.proof_wiring import (
    DEFAULT_CONTEXT_ID,
    DEFAULT_STATEMENT_ID,
    prove_private_action_mock,
    verify_private_action,
)
from l2_private_ledger.state import empty_state, state_root

from engine import FeeEngineV0

from l1_chain.devnet.adapter import (
    DeterministicInMemoryChainAdapter,
    encode_payload_set,
)
from l1_chain.types import ChainId

from wallet_kernel.keystore import InMemoryKeyStore
from wallet_kernel.kernel import WalletKernel
from wallet_kernel.secrets import SecretBytes
from wallet_kernel.signing import HMACSigner
from wallet_kernel.tx_plumbing import InMemoryNonceSource

try:
    from verifier import MockProofAdapter
except Exception as exc:  # pragma: no cover
    MockProofAdapter = None  # type: ignore
    _IMPORT_ERROR = exc


class E2EError(ValueError):
    pass


@dataclass(frozen=True)
class Summary:
    commitment_prefix: str
    fee_total: int
    tx_hash_prefix: str
    block_hash_prefix: str
    state_root_prefix: str
    receipt_hash_prefix: str


def _seed_bytes(seed: int) -> bytes:
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise E2EError("seed must be int")
    return str(seed).encode("ascii")


def _derive_root_secret(seed: int) -> bytes:
    return sha256(b"NYX:Q3:W5:ROOT:" + _seed_bytes(seed))


def _commitment(root_secret: bytes) -> bytes:
    return sha256(b"NYX:IDENTITY:COMMITMENT:v1" + root_secret)


def run_private_transfer(seed: int = 123) -> tuple[TransferTrace, Summary]:
    root_secret = _derive_root_secret(seed)
    identity_commitment = _commitment(root_secret)

    state = empty_state()
    commitment = sha256(b"NYX:PL:COMMITMENT:" + identity_commitment)
    action = LedgerAction(ActionKind.PRIVATE_MINT, PrivateMint(commitment))

    nonce = sha256(b"NYX:Q3:W5:NONCE:" + _seed_bytes(seed))
    envelope = prove_private_action_mock(
        state,
        action,
        nonce,
        witness={"note": "demo", "seed": seed},
    )

    wrong_context = sha256(b"NYX:CTX:Q3:PRIVATE_LEDGER:WRONG" + _seed_bytes(seed))
    wrong_ok = verify_private_action(
        envelope,
        state_root(state),
        action,
        context_id=wrong_context,
    )
    wrong_context_failed = not wrong_ok
    correct_ok = verify_private_action(
        envelope,
        state_root(state),
        action,
        context_id=DEFAULT_CONTEXT_ID,
        statement_id=DEFAULT_STATEMENT_ID,
    )
    if not correct_ok:
        raise E2EError("expected proof verification")

    engine = FeeEngineV0()
    action_hash = compute_action_hash(action)

    chain_id = ChainId("devnet-q3-w5")
    chain_adapter = DeterministicInMemoryChainAdapter(chain_id)

    keystore = InMemoryKeyStore()
    keystore.put_key("chain-key", SecretBytes(b"q3-w5-chain-key"))
    kernel = WalletKernel(
        chain_id=chain_id,
        keystore=keystore,
        signer=HMACSigner(),
        nonce_source=InMemoryNonceSource(salt=b"q3-w5-nonce"),
        proof_adapter=MockProofAdapter() if MockProofAdapter is not None else None,
    )

    sender = kernel.create_account("sender-q3-w5")
    kernel.add_signing_key("chain-key", keystore.get_key("chain-key"))

    payer = sender.value
    quote = quote_fee_for_private_action(
        engine,
        action,
        state_root(state),
        action_hash,
        payer=payer,
    )
    quote_b = quote_fee_for_private_action(
        engine,
        action,
        state_root(state),
        action_hash,
        payer="payer-b",
    )
    sponsor_same_amount = quote.fee_vector == quote_b.fee_vector
    if quote.fee_vector.total() <= 0:
        raise E2EError("fee total must be positive")

    receipt = enforce_fee_for_private_action(
        engine,
        quote,
        quote.fee_vector,
        payer=payer,
    )

    next_state = apply_action(state, action)
    next_root = state_root(next_state)
    key = b"pl:" + identity_commitment[:8]
    payload = encode_payload_set(key, next_root)

    request = kernel.build_action(sender=sender, payload=payload, proofs=[envelope])
    signed = kernel.sign_action(request, "chain-key")
    pre_root = chain_adapter.read_state(b"")[1].value
    tx_hash = kernel.submit(signed, chain_adapter)
    block_ref = chain_adapter.mine_block()
    post_root = chain_adapter.read_state(b"")[1].value
    if compare_digest(pre_root, post_root):
        raise E2EError("state root unchanged")

    finality = chain_adapter.get_finality(tx_hash)
    if finality is None:
        raise E2EError("finality missing")
    state_proof = chain_adapter.build_state_proof(key)
    if not chain_adapter.verify_state_proof(state_proof):
        raise E2EError("state proof invalid")

    trace = TransferTrace(
        identity=IdentityTrace(commitment_hex=identity_commitment.hex()),
        action=PrivateActionTrace(
            kind=action.kind.value,
            payload={"commitment": commitment.hex()},
            ledger_root_hex=state_root(state).hex(),
            action_hash_hex=action_hash.hex(),
        ),
        proof=ProofEnvelopeTrace.from_envelope(envelope),
        fee=FeeTrace(
            payer=payer,
            components=quote.fee_vector.canonical_obj(),
            total=quote.fee_vector.total(),
            quote_hash_hex=quote.quote_hash.hex(),
            receipt_hash_hex=receipt.receipt_hash.hex(),
            sponsor_same_amount=sponsor_same_amount,
        ),
        chain=ChainTrace(
            chain_id=chain_id.value,
            sender=sender.value,
            nonce_hex=signed.tx_envelope.nonce.hex(),
            payload_hex=payload.hex(),
            signature_hex=signed.tx_envelope.signature.value.hex(),
            tx_hash_hex=tx_hash.value.hex(),
            block_height=block_ref.height,
            block_hash_hex=block_ref.block_hash.hex(),
            state_root_before_hex=pre_root.hex(),
            state_root_after_hex=post_root.hex(),
            finality_proof_hex=finality.proof_bytes.hex(),
            state_proof=StateProofTrace(
                key_hex=key.hex(),
                value_hex=state_proof.value.hex() if state_proof.value is not None else None,
                state_root_hex=state_proof.state_root.value.hex(),
                proof_bytes_hex=state_proof.proof_bytes.hex(),
            ),
        ),
        sanity=SanityTrace(wrong_context_failed=wrong_context_failed),
    )

    summary = Summary(
        commitment_prefix=identity_commitment.hex()[:12],
        fee_total=quote.fee_vector.total(),
        tx_hash_prefix=tx_hash.value.hex()[:12],
        block_hash_prefix=block_ref.block_hash.hex()[:12],
        state_root_prefix=post_root.hex()[:12],
        receipt_hash_prefix=receipt.receipt_hash.hex()[:12],
    )

    return trace, summary
