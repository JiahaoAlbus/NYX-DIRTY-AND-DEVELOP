## Purpose
- Define the iOS Testnet Beta information architecture for the NYX world app.

## Scope
- Navigation structure and screen boundaries for wallet, exchange, marketplace, chat, entertainment, trust, and evidence views.
- Deterministic evidence display and export rules.

## Non-Scope
- No external account linking or third-party wallets.
- No live market data, no real-time network status claims.
- No mainnet guarantees or production-grade security claims.

## Navigation Model
- Primary navigation MUST use a tab bar with fixed top-level regions:
  - Home/World
  - Wallet
  - Exchange
  - Marketplace
  - Chat
  - Entertainment
  - Trust Center
- Each module MUST link to the Evidence Viewer after an action completes.

## Screen Inventory (Testnet Beta)
- Home/World: summary of available modules and testnet disclaimers.
- Wallet: address display, balance, faucet, transfer, and evidence viewer entry.
- Exchange: order entry, orderbook snapshot, trade list, evidence viewer entry.
- Marketplace: catalog, listing detail, purchase intent, evidence viewer entry.
- Chat: channel list, send message, evidence viewer entry.
- Entertainment: content list, action button, evidence viewer entry.
- Trust Center: clear rules and limitations for Testnet Beta.

## Evidence Truth Layer
- Evidence fields MUST be displayed verbatim:
  - protocol_anchor, inputs, outputs, receipt_hashes, state_hash, replay_ok, stdout
- The client MUST NOT compute or modify evidence fields.
- Export MUST be deterministic and byte-for-byte stable.

## Security and Copy Rules
- All user-facing text MUST state “Testnet Beta”.
- The app MUST NOT claim live network status or mainnet connection.
- The app MUST NOT show external balances, profiles, or identity claims.

## Freeze and Change Control
- This architecture is normative for Q10 Testnet Beta.
- Changes MUST be additive and MUST NOT alter evidence outputs.
