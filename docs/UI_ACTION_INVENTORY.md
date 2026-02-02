# NYX UI Action Inventory

This document lists all user-visible UI controls and their intended actions for both Web and iOS platforms.

## Web (nyx-world)

| Screen | Control | Action | API Call |
| :--- | :--- | :--- | :--- |
| Home | "Claim Airdrop" | Navigate to Airdrop | N/A |
| Home | "Faucet" Shortcut | Navigate to Faucet | N/A |
| Home | "Fiat" Shortcut | Navigate to Fiat | N/A |
| Home | "Airdrop" Shortcut | Navigate to Airdrop | N/A |
| Home | "Web3 Wallet" Module | Navigate to Wallet | N/A |
| Home | "Exchange" Module | Navigate to Exchange | N/A |
| Home | "Chat" Module | Navigate to Chat | N/A |
| Home | "Store" Module | Navigate to Store | N/A |
| Home | "Web2 Guard" Module | Navigate to Web2 Access | N/A |
| Onboarding | "Start Your Journey" | Generate Key & Create Account | `POST /portal/v1/accounts` |
| Faucet | "Request Tokens" | Claim NYXT tokens | `POST /wallet/v1/faucet` |
| Wallet | "Send" | Navigate to Transfer | N/A |
| Wallet | "Swap" | Navigate to Exchange | N/A |
| Wallet | "Faucet" | Navigate to Faucet | N/A |
| Exchange | "Place Order" (BUY/SELL) | Submit limit order | `POST /run` (exchange:place_order) |
| Exchange | "Cancel" | Cancel open order | `POST /run` (exchange:cancel_order) |
| Chat | "Send" | Post E2EE message | `POST /run` (chat:message_event) |
| Chat | Room List | Select active room | `GET /chat/v1/rooms/{id}/messages` |
| Store | "Buy" | Purchase item | `POST /run` (marketplace:purchase_listing) |
| Store | "List Product" | Publish new item | `POST /run` (marketplace:listing_publish) |
| Airdrop | "Claim" (Task) | Claim task reward | `POST /wallet/airdrop/claim` |
| Evidence | "Export All" | Download ZIP | `GET /export.zip` |

## iOS (nyx-ios)

| View | Control | Action | Status |
| :--- | :--- | :--- | :--- |
| NYXHomeView | "Claim Airdrop" (Banner) | N/A | Placeholder |
| NYXHomeView | "Faucet" Shortcut | N/A | Placeholder |
| NYXHomeView | "Web3 Wallet" Row | Navigate to Wallet | Functional |
| NYXHomeView | "Exchange" Row | Navigate to Exchange | Placeholder |
| NYXHomeView | "Chat" Row | Navigate to Chat | Placeholder |
| NYXHomeView | "Store" Row | Navigate to Store | Placeholder |
| NYXWalletView | "Buy" | N/A | Placeholder |
| NYXWalletView | "Send" | N/A | Placeholder |
| NYXWalletView | "Swap" | N/A | Placeholder |
| NYXWalletView | "Faucet" | N/A | Placeholder |
| NYXWalletView | Refresh (Pull/Button) | Fetch Balance | Functional (`GET /wallet/balance`) |
| NYXExchangeView | N/A | N/A | Placeholder (Static View) |
| NYXChatView | N/A | N/A | Placeholder (Static View) |
| NYXStoreView | N/A | N/A | Placeholder (Static View) |
| SettingsView | "Save Settings" | Persist Base URL | Functional |
| EvidenceCenterView | "Refresh" | List Evidence | Functional (`GET /list`) |
