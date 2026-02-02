# NYX Mainnet Parity

This document defines the differences between the NYX Testnet and the planned NYX Mainnet.

## 1. The Only Difference: Assets
The **Testnet** uses `NYXT` (NYX Testnet Token) and other testnet assets with zero real-world value. These are distributed freely via the Faucet.

The **Mainnet** will use `NYX` (Native Token) and cross-chain bridged assets with real economic value.

**Only difference is test assets vs main assets; behavior is equivalent.**

## 2. Parity Guarantees
Except for the asset value, the following components are **identical** to Mainnet standards:

- **Security Model**: Client-side E2EE for chat and non-symmetric key auth for portal access.
- **Evidence Chain**: Every state transition produces a hash-linked receipt that is verifiable and reproducible.
- **UI/UX**: The Instagram-style social experience and Binance-style trade interface are full-production grade.
- **Protocol Invariants**: Strict enforcement of fees (10 BPS), non-zero balances, and deterministic ordering.
- **iOS & Web Alignment**: Unified logic across platforms using the same Evidence Engine.

## 3. Why This Matters
By maintaining mainnet parity during the testnet phase, NYX ensures that:
1. Auditors are reviewing the actual logic that will be deployed.
2. Users are experiencing the real product flow, not a simplified demo.
3. The transition to Mainnet will be a simple "Asset Swap" rather than a code rewrite.
