# NYX Functionality Mapping Matrix (Testnet V1)

This matrix maps UI actions to backend endpoints and identifies gaps in implementation.

## Gaps Inventory

| ID | Feature | Gap Description | Impact |
| :--- | :--- | :--- | :--- |
| G01 | iOS Exchange | `NYXExchangeView` is a static placeholder with no trading logic. | High |
| G02 | iOS Chat | `NYXChatView` is a static placeholder with no messaging logic. | High |
| G03 | iOS Store | `NYXStoreView` is a static placeholder with no purchase logic. | High |
| G04 | E2EE Chat | Frontend claims E2EE but logic needs verification of real ciphertext storage. | Medium |
| G05 | Wallet Activity | Web/iOS lack a unified "Activity Feed" showing all state transitions. | Medium |
| G06 | Faucet (iOS) | Faucet UI exists in code but is not wired to any endpoint. | Medium |
| G07 | Auth (WebView) | Embedded WebView in iOS might not share auth state with native app. | Medium |
| G08 | Dapp Browser | Dapp browser exists but doesn't implement deterministic signing. | Low |
| G09 | Profile Edit | Backend supports profile updates but UI has no "Edit Profile" screen. | Low |
| G10 | Evidence Replay | UI shows evidence but lacks a "Verify Replay" button for users. | Low |

## Functionality Matrix

| UI Action | Frontend API | Backend Endpoint | MutatesState? | EvidenceGenerated? | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Create Account | `createPortalAccount` | `/portal/v1/accounts` | Yes | Yes | Fully Usable |
| Login (Auth) | `verifyPortalChallenge` | `/portal/v1/auth/verify` | Yes | Yes | Fully Usable |
| Claim Faucet | `faucetV1` | `/wallet/v1/faucet` | Yes | Yes | Fully Usable (Web + iOS) |
| Send Tokens | `transferV1` | `/wallet/v1/transfer` | Yes | Yes | Fully Usable |
| Place Order | `placeOrder` | `/run` (exchange:place_order) | Yes | Yes | Fully Usable |
| Cancel Order | `cancelOrder` | `/run` (exchange:cancel_order) | Yes | Yes | Fully Usable |
| Send Chat | `sendChatMessage` | `/run` (chat:message_event) | Yes | Yes | Fully Usable (E2EE) |
| Buy Item | `purchaseListing` | `/run` (marketplace:purchase_listing) | Yes | Yes | Fully Usable |
| List Product | `publishListing` | `/run` (marketplace:listing_publish) | Yes | Yes | Fully Usable |
| View Activity | `fetchActivity` | `/portal/v1/activity` | No | No | Fully Usable |
| Verify Replay | `fetchEvidence` | `/evidence` | No | No | Fully Usable (G10 Fix) |
| Export Proof | `downloadExportZip` | `/export.zip` | No | No | Fully Usable |
| Dapp Browser | N/A | N/A | N/A | N/A | Disabled (Requires ZK-Sig) |
