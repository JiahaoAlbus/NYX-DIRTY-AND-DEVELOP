# What NYX Is Not

## Purpose
To clearly define the boundaries of the project and prevent misconceptions during evaluation.

## Non-Goals

1.  **Not a Mainnet Blockchain**: NYX is a portal infrastructure testnet. It does not produce blocks for a public L1 chain. It produces deterministic evidence for off-chain or L2/L3 verification.
2.  **No Token Sale**: There is no NYX token for sale. Testnet tokens are free and unlimited (faucet).
3.  **No Bridge to Real Assets**: You cannot bridge mainnet ETH/BTC/USDC into NYX. All assets are testnet-only.
4.  **No KYC/AML**: The identity model is "Identity != Portal Principals". We do not collect personal data.
5.  **No Evasion**: NYX is not a privacy mixer for illicit funds. It is a technical demonstration of deterministic state transitions.
6.  **No "Fake It Till You Make It"**: We do not use mock data in the "production" paths. If the backend is down, the UI shows "Offline". We do not hardcode success responses.

## Scope Boundaries

-   **Scope**: Deterministic Gateway, Evidence Generation, Conformance Testing, Reference UI (Web/iOS).
-   **Out of Scope**: P2P Networking layer (currently centralized gateway), Consensus (currently deterministic single-sequencer for testnet), Smart Contracts (logic is hardcoded in Python modules for v1).
