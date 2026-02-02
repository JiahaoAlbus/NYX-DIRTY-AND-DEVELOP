# NYX Non-Goals

To maintain clarity for auditors and contributors, this document defines what the NYX Protocol is **NOT** trying to achieve in its current form.

## 1. Mainnet Token Launch
- NYX is a **Testnet-only** ecosystem for deterministic verification research.
- We **DO NOT** have a mainnet token.
- We **DO NOT** promise any "airdrop" value for testnet activities.
- Any mention of "NYXT" refers strictly to testnet-only accounting units with zero real-world value.

## 2. Production-Grade Scalability
- The current Gateway model is optimized for **verifiability**, not high-throughput TPS.
- We are not competing with high-performance Layer 1s or Layer 2s in terms of raw transaction speed.

## 3. Fully Permissionless Governance (Phase 1)
- During the Testnet Beta, the NYX Foundation maintains "break-glass" control over the Gateway and protocol parameters.
- Permissionless governance is a long-term goal (Phase 4), but it is **NOT** a goal for the current audit cycle.

## 4. End-User Privacy for Public Actions
- While P2P chat is encrypted, actions in the Exchange and Marketplace are **publicly observable** via the evidence chain to facilitate auditability.
- We do not aim to be a "privacy coin" or a stealth-address protocol for economic activity in this phase.

## 5. Arbitrary Smart Contract Execution
- NYX uses a **Module-based execution** model (Wallet, Exchange, etc.).
- It does not support arbitrary EVM or WASM smart contracts to ensure strict determinism and auditability of core modules.
