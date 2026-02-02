# Release Notes: NYX Testnet Portal v1.0.0

## 🚀 Overview
This release marks the transition from a "Demo" state to a "Mainnet-Equivalent" product ecosystem. Every component has been upgraded to support deterministic execution, cryptographic evidence, and production-grade UI.

## 💎 New Features

### 1. Unified Identity System
- Identity is now logically separated from Account addresses.
- Multi-account switching support.
- Non-symmetric key authentication (Challenge-Response).

### 2. Instagram-Style Chat (E2EE)
- Client-side AES-GCM encryption.
- Backend stores only ciphertexts.
- Verifiable hash-chain for message ordering.
- IG-style Stories and Direct Message layout.

### 3. Binance-Style Exchange
- Real matching engine with balance settlement.
- Support for Limit/Market orders.
- Fixed 10 BPS protocol fee routed to treasury.
- Real-time order book and trade history.

### 4. Taobao-Style Store
- Real product publishing and purchasing.
- Payment → Evidence → Settlement flow.
- Purchase history backed by evidence bundles.

### 5. Deterministic Wallet
- Multi-asset support (NYXT, etc.).
- Real faucet with anti-sybil logic.
- Transfer history reproducible via evidence replay.

## 🧱 Protocol Hardening
- All state mutations now route through the Evidence Engine.
- Forbidden "mock/fake" patterns have been purged from core logic.
- Full verification suite included in `scripts/`.

## 📦 Artifacts Included
- Web Bundle (`nyx-portal-dist.zip`)
- iOS App (Simulator & Device)
- Chrome Extension (Wallet)
- Backend Tarball
