import { bytesToBase64, encodeUtf8 } from "./utils";
import { hmac } from "@noble/hashes/hmac";
import { sha256 } from "@noble/hashes/sha256";

export type BackendStatus = "unknown" | "online" | "offline";

export interface EvidenceBundle {
  protocol_anchor: string;
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown>;
  receipt_hashes: string[];
  state_hash: string;
  replay_ok: boolean;
  stdout: string;
}

export interface PortalSession {
  account_id: string;
  handle: string;
  pubkey: string;
  access_token: string;
}

declare global {
  interface Window {
    __NYX_BACKEND_URL__?: string;
  }
}

export const DEFAULT_BACKEND_URL = "http://127.0.0.1:8091";

export function getBackendUrl(): string {
  if (typeof window !== "undefined" && window.__NYX_BACKEND_URL__) {
    return window.__NYX_BACKEND_URL__ as string;
  }
  return DEFAULT_BACKEND_URL;
}

async function requestJson<T>(
  path: string,
  options?: RequestInit,
  baseUrl?: string
): Promise<T> {
  const url = `${baseUrl ?? getBackendUrl()}${path}`;
  const response = await fetch(url, options);
  const text = await response.text();
  let payload: unknown = {};
  if (text.trim().length > 0) {
    payload = JSON.parse(text);
  }
  if (!response.ok) {
    const message = (payload as { error?: string }).error || `HTTP ${response.status}`;
    throw new Error(message);
  }
  return payload as T;
}

export async function checkHealth(baseUrl?: string): Promise<boolean> {
  try {
    const payload = await requestJson<{ ok?: boolean }>("/healthz", undefined, baseUrl);
    return payload.ok === true;
  } catch {
    return false;
  }
}

export async function fetchCapabilities(): Promise<Record<string, unknown>> {
  return requestJson<Record<string, unknown>>("/capabilities");
}

export function derivePortalKey(seed: string): { pubkey: string; keyBytes: Uint8Array } {
  const seedBytes = sha256(encodeUtf8(seed));
  const pubkey = bytesToBase64(seedBytes);
  return { pubkey, keyBytes: seedBytes };
}

export async function createPortalAccount(handle: string, pubkey: string) {
  return requestJson<{ account_id: string; handle: string; pubkey: string; created_at: number; status: string }>(
    "/portal/v1/accounts",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ handle, pubkey }),
    }
  );
}

export async function fetchPortalChallenge(accountId: string) {
  return requestJson<{ nonce: string; expires_at: number }>(
    "/portal/v1/auth/challenge",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ account_id: accountId }),
    }
  );
}

export async function verifyPortalChallenge(accountId: string, nonce: string, keyBytes: Uint8Array) {
  const signature = bytesToBase64(hmac(sha256, keyBytes, encodeUtf8(nonce)));
  return requestJson<{ access_token: string; expires_at: number }>(
    "/portal/v1/auth/verify",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ account_id: accountId, nonce, signature }),
    }
  );
}

export async function logoutPortal(accessToken: string) {
  return requestJson<{ ok: boolean }>(
    "/portal/v1/auth/logout",
    {
      method: "POST",
      headers: { Authorization: `Bearer ${accessToken}` },
    }
  );
}

export async function fetchPortalMe(accessToken: string) {
  return requestJson<Record<string, unknown>>("/portal/v1/me", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

export async function fetchActivity(accessToken: string, limit: number = 50, offset: number = 0) {
  return requestJson<{ account_id: string; receipts: Record<string, unknown>[]; limit: number; offset: number }>(
    `/portal/v1/activity?limit=${limit}&offset=${offset}`,
    { headers: { Authorization: `Bearer ${accessToken}` } }
  );
}

export async function fetchEvidence(runId: string): Promise<EvidenceBundle> {
  return requestJson<EvidenceBundle>(`/evidence?run_id=${encodeURIComponent(runId)}`);
}

export async function downloadExportZip(runId: string): Promise<Blob> {
  const url = `${getBackendUrl()}/export.zip?run_id=${encodeURIComponent(runId)}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return await response.blob();
}

export async function fetchWalletBalance(address: string) {
  return requestJson<{ address: string; balance: number }>(
    `/wallet/balance?address=${encodeURIComponent(address)}`
  );
}

export async function transferWallet(token: string, fromAddress: string, toAddress: string, amount: number, assetId: string = 'NYXT') {
  const payload = {
    seed: Math.floor(Math.random() * 1000000),
    run_id: `xfer-${Date.now()}`,
    payload: {
      from_address: fromAddress,
      to_address: toAddress,
      amount,
      asset_id: assetId
    }
  };
  return requestJson<Record<string, unknown>>('/wallet/v1/transfer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
    body: JSON.stringify(payload)
  });
}

export async function faucetWallet(token: string, address: string, amount: number = 1000000000, assetId: string = 'NYXT') {
  const payload = {
    seed: Math.floor(Math.random() * 1000000),
    run_id: `faucet-${Date.now()}`,
    payload: {
      address,
      amount,
      asset_id: assetId
    }
  };
  return requestJson<Record<string, unknown>>('/wallet/v1/faucet', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
    body: JSON.stringify(payload)
  });
}

export async function placeOrder(token: string, ownerAddress: string, side: 'BUY' | 'SELL', amount: number, price: number, assetIn: string, assetOut: string) {
  const payload = {
    seed: Math.floor(Math.random() * 1000000),
    run_id: `order-${Date.now()}`,
    module: 'exchange',
    action: 'place_order',
    payload: {
      owner_address: ownerAddress,
      side,
      amount,
      price,
      asset_in: assetIn,
      asset_out: assetOut
    }
  };
  return requestJson<Record<string, unknown>>('/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
    body: JSON.stringify(payload)
  });
}

export async function cancelOrder(token: string, orderId: string) {
  const payload = {
    seed: Math.floor(Math.random() * 1000000),
    run_id: `cancel-${Date.now()}`,
    module: "exchange",
    action: "cancel_order",
    payload: { order_id: orderId },
  };
  return requestJson<Record<string, unknown>>("/run", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
}

export async function fetchOrderBook() {
  return requestJson<Record<string, unknown>>("/exchange/orderbook");
}

export async function fetchOrders() {
  return requestJson<{ orders: Record<string, unknown>[] }>("/exchange/orders");
}

export async function fetchTrades() {
  return requestJson<{ trades: Record<string, unknown>[] }>("/exchange/trades");
}

export async function listChatRooms(accessToken: string) {
  return requestJson<{ rooms: Record<string, unknown>[] }>("/chat/v1/rooms", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

export async function createChatRoom(accessToken: string, name: string, isPublic: boolean = true) {
  return requestJson<Record<string, unknown>>("/chat/v1/rooms", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ name, is_public: isPublic }),
  });
}

export async function listChatMessages(accessToken: string, roomId: string) {
  return requestJson<{ messages: Record<string, unknown>[] }>(
    `/chat/v1/rooms/${encodeURIComponent(roomId)}/messages`,
    { headers: { Authorization: `Bearer ${accessToken}` } }
  );
}

/**
 * E2EE Helper for Chat
 */
const ENCRYPTION_KEY_PREFIX = "nyx_chat_key_";

async function getEncryptionKey(roomId: string): Promise<CryptoKey> {
  const keyMaterial = await window.crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(`NYX_SECRET_${roomId}`),
    { name: "PBKDF2" },
    false,
    ["deriveKey"]
  );
  return window.crypto.subtle.deriveKey(
    {
      name: "PBKDF2",
      salt: new TextEncoder().encode("NYX_SALT"),
      iterations: 100000,
      hash: "SHA-256",
    },
    keyMaterial,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"]
  );
}

export async function encryptMessage(roomId: string, text: string): Promise<string> {
  const key = await getEncryptionKey(roomId);
  const iv = window.crypto.getRandomValues(new Uint8Array(12));
  const encrypted = await window.crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    key,
    new TextEncoder().encode(text)
  );
  const combined = new Uint8Array(iv.length + encrypted.byteLength);
  combined.set(iv);
  combined.set(new Uint8Array(encrypted), iv.length);
  return `E2EE:${btoa(String.fromCharCode(...combined))}`;
}

export async function decryptMessage(roomId: string, ciphertext: string): Promise<string> {
  if (!ciphertext.startsWith("E2EE:")) return ciphertext;
  try {
    const key = await getEncryptionKey(roomId);
    const combined = new Uint8Array(atob(ciphertext.replace("E2EE:", "")).split("").map(c => c.charCodeAt(0)));
    const iv = combined.slice(0, 12);
    const encrypted = combined.slice(12);
    const decrypted = await window.crypto.subtle.decrypt(
      { name: "AES-GCM", iv },
      key,
      encrypted
    );
    return new TextDecoder().decode(decrypted);
  } catch (err) {
    return "[Decryption Failed]";
  }
}

export async function sendChatMessage(accessToken: string, roomId: string, body: string) {
  const ciphertext = await encryptMessage(roomId, body);
  const payload = {
    seed: Math.floor(Math.random() * 1000000),
    run_id: `chat-${Date.now()}`,
    module: "chat",
    action: "message_event",
    payload: {
      channel: roomId,
      message: ciphertext
    }
  };
  return requestJson<Record<string, unknown>>("/run", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(payload),
  });
}

export async function listMarketplaceListings() {
  return requestJson<{ listings: Record<string, unknown>[] }>("/marketplace/listings");
}

export async function listMarketplacePurchases() {
  return requestJson<{ purchases: Record<string, unknown>[] }>("/marketplace/purchases");
}

export async function publishListing(token: string, publisherId: string, sku: string, title: string, price: number) {
  const payload = {
    seed: Math.floor(Math.random() * 1000000),
    run_id: `list-${Date.now()}`,
    module: 'marketplace',
    action: 'listing_publish',
    payload: {
      publisher_id: publisherId,
      sku,
      title,
      price
    }
  };
  return requestJson<Record<string, unknown>>('/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
    body: JSON.stringify(payload)
  });
}

export async function purchaseMarketplace(token: string, buyerId: string, listingId: string, qty: number) {
  const payload = {
    seed: Math.floor(Math.random() * 1000000),
    run_id: `buy-${Date.now()}`,
    module: 'marketplace',
    action: 'purchase_listing',
    payload: {
      buyer_id: buyerId,
      listing_id: listingId,
      qty
    }
  };
  return requestJson<Record<string, unknown>>('/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
    body: JSON.stringify(payload)
  });
}

export async function fetchDiscoveryFeed() {
  return requestJson<{ feed: { type: string; data: any }[] }>("/discovery/feed");
}

export async function claimAirdrop(token: string, address: string, taskId: string, reward: number) {
  const payload = {
    seed: Math.floor(Math.random() * 1000000),
    run_id: `airdrop-${Date.now()}`,
    payload: {
      address,
      task_id: taskId,
      reward
    }
  };
  return requestJson<Record<string, unknown>>('/wallet/airdrop/claim', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
    body: JSON.stringify(payload)
  });
}

export async function listEntertainmentItems() {
  return requestJson<{ items: Record<string, unknown>[] }>("/entertainment/items");
}

export async function listEntertainmentEvents() {
  return requestJson<{ events: Record<string, unknown>[] }>("/entertainment/events");
}

export async function postEntertainmentStep(payload: Record<string, unknown>, seed: number, runId: string) {
  return requestJson<Record<string, unknown>>("/entertainment/step", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ seed, run_id: runId, payload }),
  });
}
