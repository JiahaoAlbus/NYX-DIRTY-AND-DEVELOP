# NYX Backend Endpoint Inventory

This document lists all available backend endpoints, their methods, schemas, and evidence status.

## Core API

| Route | Method | Module | Action | Mutation? | Evidence? | Auth? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `/healthz` | GET | System | health | No | No | No |
| `/version` | GET | System | version | No | No | No |
| `/capabilities` | GET | System | capabilities | No | No | No |
| `/run` | POST | Varied | Varied | Yes | Yes | No |
| `/status` | GET | Evidence | status | No | No | No |
| `/evidence` | GET | Evidence | load | No | No | No |
| `/artifact` | GET | Evidence | artifact | No | No | No |
| `/export.zip` | GET | Evidence | export | No | No | No |
| `/list` | GET | Evidence | list | No | No | No |

## Portal Module

| Route | Method | Description | Mutation? | Auth? |
| :--- | :--- | :--- | :--- | :--- |
| `/portal/v1/accounts` | POST | Create account | Yes | No |
| `/portal/v1/auth/challenge` | POST | Request auth challenge | Yes | No |
| `/portal/v1/auth/verify` | POST | Verify challenge & get token | Yes | No |
| `/portal/v1/auth/logout` | POST | Invalidate session | Yes | Yes |
| `/portal/v1/me` | GET | Get current account info | No | Yes |
| `/portal/v1/profile` | POST | Update handle/bio | Yes | Yes |
| `/portal/v1/activity` | GET | List account receipts | No | Yes |
| `/portal/v1/rooms/search` | GET | Search chat rooms | No | Yes |

## Wallet Module

| Route | Method | Description | Mutation? | Auth? |
| :--- | :--- | :--- | :--- | :--- |
| `/wallet/balance` | GET | Get address balance | No | No |
| `/wallet/faucet` | POST | Claim test tokens (Legacy) | Yes | No |
| `/wallet/v1/faucet` | POST | Claim test tokens (V1) | Yes | Yes |
| `/wallet/transfer` | POST | Send tokens (Legacy) | Yes | No |
| `/wallet/v1/transfer` | POST | Send tokens (V1) | Yes | Yes |
| `/wallet/airdrop/claim` | POST | Claim airdrop rewards | Yes | No |

## Exchange Module

| Route | Method | Description | Mutation? | Auth? |
| :--- | :--- | :--- | :--- | :--- |
| `/exchange/orderbook` | GET | Get bid/ask lists | No | No |
| `/exchange/orders` | GET | List open orders | No | No |
| `/exchange/trades` | GET | List recent trades | No | No |
| `/exchange/place_order` | POST | Submit new order | Yes | No |
| `/exchange/cancel_order` | POST | Cancel existing order | Yes | No |

## Marketplace Module

| Route | Method | Description | Mutation? | Auth? |
| :--- | :--- | :--- | :--- | :--- |
| `/marketplace/listings` | GET | List active listings | No | No |
| `/marketplace/listings/search` | GET | Search listings | No | No |
| `/marketplace/purchases` | GET | List purchase history | No | No |
| `/marketplace/listing` | POST | Publish new listing | Yes | No |
| `/marketplace/purchase` | POST | Execute purchase | Yes | No |

## Integrations Module

| Route | Method | Description | Mutation? | Auth? |
| :--- | :--- | :--- | :--- | :--- |
| `/integrations/v1/0x/quote` | GET | 0x swap quote | No | Yes |
| `/integrations/v1/jupiter/quote` | GET | Jupiter swap quote | No | Yes |
| `/integrations/v1/magic_eden/solana/collections` | GET | Magic Eden Solana collections (public; optional API key header) | No | Yes |
| `/integrations/v1/magic_eden/solana/collection_listings` | GET | Magic Eden Solana collection listings (public; optional API key header) | No | Yes |
| `/integrations/v1/magic_eden/solana/token` | GET | Magic Eden Solana token detail (public; optional API key header) | No | Yes |
| `/integrations/v1/magic_eden/evm/collections/search` | GET | Magic Eden EVM collections search (public; optional API key header) | No | Yes |
| `/integrations/v1/magic_eden/evm/collections` | GET | Magic Eden EVM collections by slug/id (public; optional API key header) | No | Yes |

## Chat Module

| Route | Method | Description | Mutation? | Auth? |
| :--- | :--- | :--- | :--- | :--- |
| `/chat/v1/rooms` | POST | Create chat room | Yes | Yes |
| `/chat/v1/rooms` | GET | List chat rooms | No | Yes |
| `/chat/v1/rooms/{id}/messages` | POST | Post message to room | Yes | Yes |
| `/chat/v1/rooms/{id}/messages` | GET | List messages in room | No | Yes |
| `/chat/send` | POST | Send legacy message | Yes | No |
| `/chat/messages` | GET | List legacy messages | No | No |

## Web2 Guard Module

| Route | Method | Description | Mutation? | Auth? |
| :--- | :--- | :--- | :--- | :--- |
| `/web2/v1/allowlist` | GET | List approved Web2 endpoints | No | No |
| `/web2/v1/request` | POST | Execute guarded Web2 request (evidence + fee) | Yes | Yes |
| `/web2/v1/requests` | GET | List guarded requests (per account) | No | Yes |

## Entertainment Module

| Route | Method | Description | Mutation? | Auth? |
| :--- | :--- | :--- | :--- | :--- |
| `/entertainment/items` | GET | List items | No | No |
| `/entertainment/events` | GET | List events | No | No |
| `/entertainment/step` | POST | Advance item state | Yes | No |
