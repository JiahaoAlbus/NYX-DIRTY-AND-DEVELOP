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

export async function listEvidenceRuns() {
  return requestJson<{ runs: { run_id: string; status: string }[] }>("/list");
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

export async function faucetV1(accessToken: string, payload: Record<string, unknown>, seed: number, runId: string) {
  return requestJson<Record<string, unknown>>("/wallet/v1/faucet", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ seed, run_id: runId, payload }),
  });
}

export async function transferV1(accessToken: string, payload: Record<string, unknown>, seed: number, runId: string) {
  return requestJson<Record<string, unknown>>("/wallet/v1/transfer", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ seed, run_id: runId, payload }),
  });
}

export async function placeOrder(payload: Record<string, unknown>, seed: number, runId: string) {
  return requestJson<Record<string, unknown>>("/exchange/place_order", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ seed, run_id: runId, payload }),
  });
}

export async function cancelOrder(payload: Record<string, unknown>, seed: number, runId: string) {
  return requestJson<Record<string, unknown>>("/exchange/cancel_order", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ seed, run_id: runId, payload }),
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

export async function createChatRoom(accessToken: string, name: string, isPublic: boolean) {
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

export async function sendChatMessage(accessToken: string, roomId: string, body: string) {
  return requestJson<Record<string, unknown>>(`/chat/v1/rooms/${encodeURIComponent(roomId)}/messages`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ body }),
  });
}

export async function listMarketplaceListings() {
  return requestJson<{ listings: Record<string, unknown>[] }>("/marketplace/listings");
}

export async function createMarketplaceListing(payload: Record<string, unknown>, seed: number, runId: string) {
  return requestJson<Record<string, unknown>>("/marketplace/listing", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ seed, run_id: runId, payload }),
  });
}

export async function purchaseMarketplace(payload: Record<string, unknown>, seed: number, runId: string) {
  return requestJson<Record<string, unknown>>("/marketplace/purchase", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ seed, run_id: runId, payload }),
  });
}

export async function listMarketplacePurchases() {
  return requestJson<{ purchases: Record<string, unknown>[] }>("/marketplace/purchases");
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
