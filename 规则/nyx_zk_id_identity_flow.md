# NYX ZK-ID — Identity Lifecycle Flow (Textual)

> **Status**: Week 3 Deliverable  
> **Nature**: Descriptive (Non-Normative)  
> **Authoritative Rules**: `NYX_ZK-ID_Spec_v1.md`

This document describes the NYX ZK-ID lifecycle as a **conceptual flow**.

It introduces no rules, permissions, or guarantees.  
All normative authority resides exclusively in the Spec.

---

## 1. Identity Generation (Generate)

```
[Start]
   |
   |-- Subject locally generates Root Secret (RS)
   |-- No KYC, no platform account, no trusted operator
   |-- Wallets may store keys but do not define identity
   |-- (Optional) On-chain anchors created
   |
[Identity State: Active]
```

**Notes**
- Pure local generation does not incur protocol cost.
- Any on-chain anchor creation implies protocol state mutation and associated cost.
- Generation does not imply uniqueness or personhood.

---

## 2. Identity Usage (Prove / Verify)

```
[Active Identity]
   |
   |-- Subject selects Context
   |-- Subject selects Claim
   |-- Zero-knowledge proof generated
   |-- Proof bound to Context
   |
[Verifier]
   |
   |-- Verifier checks proof
   |-- Learns only claim satisfaction
   |
[Context Ends]
```

**Notes**
- Proofs are valid only within their originating context.
- Proof outputs are non-identifying.

---

## 3. Identity Rotation (Rotate)

```
[Active Identity]
   |
   |-- Rotation trigger (hygiene / compromise / migration)
   |-- New cryptographic material generated
   |-- Lineage proof executed
   |-- Old material retired
   |
[Active Identity (Rotated)]
```

**Notes**
- Lineage proves continuity but is never reusable.
- Rotation does not introduce new identities.

---

## 4. Identity Destruction (Destroy)

```
[Active Identity]
   |
   |-- Destruction initiated
   |-- Identity state marked destroyed
   |
[Identity State: Destroyed]
```

**Notes**
- Destroyed identities permanently fail verification.
- Destruction is irreversible.

---

## 5. Identity Recovery (Recover)

```
[Lost Access]
   |
   |-- Recovery mechanism activated
   |-- New Root Secret established
   |-- Lineage to prior identity proven
   |
[Active Identity (Recovered)]
```

**Notes**
- Recovery restores control, not old keys.
- No administrators or trusted agents are involved.

---

## 6. Lifecycle Summary

```
Generate → Active → Use ↔ Rotate → Destroy
                 ↘ Recover
```

**Key Takeaway**
- Identity continuity is logical, not key-based.
- Privacy emerges from structure, not policy.

---

## Relationship to the Spec

If any interpretation in this document conflicts with the Spec, the Spec prevails.

---

**End of Document**

