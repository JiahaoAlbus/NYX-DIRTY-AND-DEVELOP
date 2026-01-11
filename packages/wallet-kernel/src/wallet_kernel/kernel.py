from __future__ import annotations

from dataclasses import dataclass, field

from l1_chain.adapter import ChainAdapter
from l1_chain.types import ChainAccount, ChainId, TxEnvelope, TxHash

from wallet_kernel.canonical import require_text
from wallet_kernel.errors import PolicyError, ProofError, ValidationError
from wallet_kernel.keystore import KeyStore
from wallet_kernel.policy import ActionPolicy, Capability, DenyAllPolicy
from wallet_kernel.proof_plumbing import ProofBundle, ProofCarrier, ProofVerifier
from wallet_kernel.signing import Signer
from wallet_kernel.tx_plumbing import NonceSource, TxBuilder


@dataclass(frozen=True)
class TxRequest:
    chain_id: ChainId
    sender: ChainAccount
    bundle: ProofBundle
    requires_capability: bool
    capability: Capability | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.chain_id, ChainId):
            raise ValidationError("chain_id must be ChainId")
        if not isinstance(self.sender, ChainAccount):
            raise ValidationError("sender must be ChainAccount")
        if not isinstance(self.bundle, ProofBundle):
            raise ValidationError("bundle must be ProofBundle")
        if not isinstance(self.requires_capability, bool):
            raise ValidationError("requires_capability must be bool")
        if self.requires_capability and self.capability is None:
            raise ValidationError("capability required")
        if self.capability is not None and not isinstance(self.capability, Capability):
            raise ValidationError("capability must be Capability")

    @property
    def payload(self) -> bytes:
        return self.bundle.payload

    @property
    def proofs(self) -> tuple:
        return self.bundle.proofs


@dataclass(frozen=True)
class SignedTx:
    request: TxRequest
    tx_envelope: TxEnvelope

    def __post_init__(self) -> None:
        if not isinstance(self.request, TxRequest):
            raise ValidationError("request must be TxRequest")
        if not isinstance(self.tx_envelope, TxEnvelope):
            raise ValidationError("tx_envelope must be TxEnvelope")

    @property
    def tx_hash(self) -> TxHash:
        return self.tx_envelope.tx_hash


@dataclass(frozen=True)
class WalletKernel:
    chain_id: ChainId
    keystore: KeyStore
    signer: Signer
    nonce_source: NonceSource
    policy: ActionPolicy = field(default_factory=DenyAllPolicy)
    proof_adapter: object | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.chain_id, ChainId):
            raise ValidationError("chain_id must be ChainId")
        if not isinstance(self.keystore, KeyStore):
            raise ValidationError("keystore must be KeyStore")
        if not isinstance(self.signer, Signer):
            raise ValidationError("signer must be Signer")
        if not isinstance(self.nonce_source, NonceSource):
            raise ValidationError("nonce_source must be NonceSource")
        if not isinstance(self.policy, ActionPolicy):
            raise ValidationError("policy must be ActionPolicy")

    def create_account(self, label: str) -> ChainAccount:
        name = require_text(label, "label")
        return ChainAccount(name)

    def add_signing_key(self, key_id: str, secret) -> None:
        self.keystore.put_key(key_id, secret)

    def build_action(
        self,
        *,
        sender: ChainAccount,
        payload: bytes,
        proofs=None,
        requires_capability: bool = False,
        capability: Capability | None = None,
    ) -> TxRequest:
        if not isinstance(sender, ChainAccount):
            raise ValidationError("sender must be ChainAccount")
        if not isinstance(payload, bytes):
            raise ValidationError("payload must be bytes")
        bundle = ProofCarrier.attach(payload, proofs)
        return TxRequest(
            chain_id=self.chain_id,
            sender=sender,
            bundle=bundle,
            requires_capability=requires_capability,
            capability=capability,
        )

    def sign_action(self, request: TxRequest, key_id: str) -> SignedTx:
        if not isinstance(request, TxRequest):
            raise ValidationError("request must be TxRequest")
        if request.chain_id.value != self.chain_id.value:
            raise ValidationError("chain_id mismatch")
        if request.requires_capability:
            if not self.policy.authorize(request, request.capability):
                raise PolicyError("capability denied")
        builder = TxBuilder(
            keystore=self.keystore,
            signer=self.signer,
            nonce_source=self.nonce_source,
        )
        tx = builder.build_and_sign_tx(
            chain_id=request.chain_id,
            sender=request.sender,
            key_id=key_id,
            payload=request.payload,
        )
        return SignedTx(request=request, tx_envelope=tx)

    def submit(self, signed_tx: SignedTx, chain_adapter: ChainAdapter) -> TxHash:
        if not isinstance(signed_tx, SignedTx):
            raise ValidationError("signed_tx must be SignedTx")
        if not isinstance(chain_adapter, ChainAdapter):
            raise ValidationError("chain_adapter must be ChainAdapter")
        return chain_adapter.submit_tx(signed_tx.tx_envelope)

    def verify_proofs(
        self,
        proofs,
        expected_context_id: bytes,
        expected_statement_id: str,
    ) -> bool:
        if self.proof_adapter is None:
            raise ProofError("proof adapter required")
        verifier = ProofVerifier(self.proof_adapter)
        if proofs is None:
            proof_list: tuple = ()
        else:
            proof_list = tuple(proofs)
        return verifier.verify_all(proof_list, expected_context_id, expected_statement_id)
