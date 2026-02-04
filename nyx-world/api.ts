import { bytesToBase64, encodeUtf8 } from "./utils";
import { hmac } from "@noble/hashes/hmac";
import { sha256 } from "@noble/hashes/sha256";
import type { Capabilities } from "./capabilities";
import type { Web2AllowlistEntry, Web2GuardRequestRow, Web2GuardResponse } from "./types";

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

export type ApiErrorDetails = Record<string, unknown>;

export class ApiError extends Error {
  status: number;
  code: string;
  details?: ApiErrorDetails;

  constructor(status: number, code: string, message: string, details?: ApiErrorDetails) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
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

export function parseSeed(seed: string): number {
  const value = Number(seed);
  if (!Number.isInteger(value) || value < 0) {
    throw new Error("Seed must be a non-negative integer.");
  }
  return value;
}

const RUN_COUNTER_PREFIX = "nyx_run_counter_";
const fallbackRunCounters: Record<string, number> = {};

export function allocateRunId(baseRunId: string, action: string): string {
  const safeBase = (baseRunId || "").trim() || "run";
  const safeAction = (action || "action").replace(/[^a-zA-Z0-9_-]/g, "_");
  const storageKey = `${RUN_COUNTER_PREFIX}${safeBase}`;

  let next = 1;
  try {
    const currentRaw = localStorage.getItem(storageKey);
    const current = currentRaw ? Number(currentRaw) : 0;
    next = Number.isFinite(current) ? current + 1 : 1;
    localStorage.setItem(storageKey, String(next));
  } catch {
    const fallbackKey = `${safeBase}:${safeAction}`;
    next = (fallbackRunCounters[fallbackKey] ?? 0) + 1;
    fallbackRunCounters[fallbackKey] = next;
  }
  return `${safeBase}-${safeAction}-${next}`;
}

type RequestJsonOptions = {
  method?: string;
  headers?: Record<string, string>;
  token?: string;
  body?: unknown;
  timeoutMs?: number;
  retry?: boolean;
  baseUrl?: string;
};

function isIdempotent(method: string): boolean {
  return ["GET", "HEAD"].includes(method.toUpperCase());
}

async function requestJson<T>(path: string, options: RequestJsonOptions = {}): Promise<T> {
  const method = (options.method ?? "GET").toUpperCase();
  const baseUrl = options.baseUrl ?? getBackendUrl();
  const url = `${baseUrl}${path}`;
  const timeoutMs = options.timeoutMs ?? 10_000;
  const retry = options.retry ?? true;

  const headers: Record<string, string> = { ...(options.headers ?? {}) };
  if (options.token) headers.Authorization = `Bearer ${options.token}`;
  if (options.body !== undefined && headers["Content-Type"] === undefined) {
    headers["Content-Type"] = "application/json";
  }

  const attempt = async (): Promise<T> => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(url, {
        method,
        headers,
        body: options.body === undefined ? undefined : JSON.stringify(options.body),
        signal: controller.signal,
      });
      const text = await response.text();
      const payload: unknown = text.trim().length ? (() => { try { return JSON.parse(text); } catch { return { error: text }; } })() : {};

      if (!response.ok) {
        let code = `HTTP_${response.status}`;
        let message = `HTTP ${response.status}`;
        let details: ApiErrorDetails | undefined = undefined;

        if (payload && typeof payload === "object" && "error" in (payload as any)) {
          const err = (payload as any).error;
          if (typeof err === "string") {
            message = err;
          } else if (err && typeof err === "object") {
            code = String((err as any).code ?? code);
            message = String((err as any).message ?? message);
            const rawDetails = (err as any).details;
            if (rawDetails && typeof rawDetails === "object") {
              details = rawDetails as ApiErrorDetails;
            }
          }
        }
        throw new ApiError(response.status, code, message, details);
      }
      return payload as T;
    } finally {
      clearTimeout(timeout);
    }
  };

  const maxAttempts = retry && isIdempotent(method) ? 2 : 1;
  let lastError: unknown;
  for (let i = 0; i < maxAttempts; i++) {
    try {
      return await attempt();
    } catch (err) {
      lastError = err;
      if (i + 1 >= maxAttempts) break;
      await new Promise((resolve) => setTimeout(resolve, 250));
    }
  }
  throw lastError;
}

export async function checkHealth(baseUrl?: string): Promise<boolean> {
  try {
    const payload = await requestJson<{ ok?: boolean }>("/healthz", { baseUrl, retry: false, timeoutMs: 3_000 });
    return payload.ok === true;
  } catch {
    return false;
  }
}

export async function fetchCapabilities(): Promise<Capabilities> {
  return requestJson<Capabilities>("/capabilities");
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
      body: { handle, pubkey },
      retry: false,
    }
  );
}

export async function fetchPortalChallenge(accountId: string) {
  return requestJson<{ nonce: string; expires_at: number }>("/portal/v1/auth/challenge", {
    method: "POST",
    body: { account_id: accountId },
    retry: false,
  });
}

export async function verifyPortalChallenge(accountId: string, nonce: string, keyBytes: Uint8Array) {
  const signature = bytesToBase64(hmac(sha256, keyBytes, encodeUtf8(nonce)));
  return requestJson<{ access_token: string; expires_at: number }>("/portal/v1/auth/verify", {
    method: "POST",
    body: { account_id: accountId, nonce, signature },
    retry: false,
  });
}

export async function logoutPortal(accessToken: string) {
  return requestJson<{ ok: boolean }>("/portal/v1/auth/logout", {
    method: "POST",
    token: accessToken,
    retry: false,
  });
}

export async function fetchPortalMe(accessToken: string) {
  return requestJson<{ account_id: string; handle: string; pubkey: string; created_at: number; status: string }>(
    "/portal/v1/me",
    { token: accessToken, retry: false }
  );
}

export async function fetchPortalAccountById(accessToken: string, accountId: string) {
  return requestJson<{ account: { account_id: string; handle: string; public_jwk: JsonWebKey | null } }>(
    `/portal/v1/accounts/by_id?account_id=${encodeURIComponent(accountId)}`,
    { token: accessToken, retry: false }
  );
}

export async function fetchActivity(accessToken: string, limit: number = 50, offset: number = 0) {
  return requestJson<{ account_id: string; receipts: Record<string, unknown>[]; limit: number; offset: number }>(
    `/portal/v1/activity?limit=${limit}&offset=${offset}`,
    { token: accessToken }
  );
}

export async function fetchEvidence(runId: string): Promise<EvidenceBundle> {
  return requestJson<EvidenceBundle>(`/evidence?run_id=${encodeURIComponent(runId)}`, { retry: true });
}

export interface EvidenceReplayResultV1 {
  run_id: string;
  ok: boolean;
  recorded: Record<string, unknown>;
  replayed: Record<string, unknown>;
  diff: Record<string, unknown>;
}

export async function verifyEvidenceReplayV1(token: string, runId: string): Promise<EvidenceReplayResultV1> {
  return requestJson<EvidenceReplayResultV1>("/evidence/v1/replay", {
    method: "POST",
    token,
    body: { run_id: runId },
    retry: false,
  });
}

export async function downloadExportZip(runId: string): Promise<Blob> {
  const url = `${getBackendUrl()}/export.zip?run_id=${encodeURIComponent(runId)}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new ApiError(response.status, `HTTP_${response.status}`, `HTTP ${response.status}`);
  }
  return await response.blob();
}

export async function downloadProofZip(token: string, prefix: string, limit: number = 200): Promise<Blob> {
  const url = `${getBackendUrl()}/proof.zip?prefix=${encodeURIComponent(prefix)}&limit=${limit}`;
  const response = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  if (!response.ok) {
    const text = await response.text();
    let message = `HTTP ${response.status}`;
    try {
      const payload = JSON.parse(text);
      if (payload?.error?.message) message = String(payload.error.message);
    } catch {
      // ignore
    }
    throw new ApiError(response.status, `HTTP_${response.status}`, message);
  }
  return await response.blob();
}

export async function fetchWeb2Allowlist() {
  return requestJson<{ allowlist: Web2AllowlistEntry[] }>("/web2/v1/allowlist", { retry: false });
}

export async function fetchWeb2Requests(token: string, limit: number = 25, offset: number = 0) {
  const qs = new URLSearchParams();
  qs.set("limit", String(limit));
  qs.set("offset", String(offset));
  return requestJson<{ requests: Web2GuardRequestRow[]; limit: number; offset: number }>(
    `/web2/v1/requests?${qs.toString()}`,
    { token }
  );
}

export async function executeWeb2GuardRequest(
  token: string,
  seed: number,
  runId: string,
  payload: { url: string; method?: string; body?: string | Record<string, unknown>; sealed_request?: string }
): Promise<Web2GuardResponse> {
  return requestJson<Web2GuardResponse>("/web2/v1/request", {
    method: "POST",
    token,
    body: { seed, run_id: runId, payload },
    retry: false,
  });
}

export async function fetchWalletBalance(address: string, assetId: string = "NYXT") {
  const query = `address=${encodeURIComponent(address)}&asset_id=${encodeURIComponent(assetId)}`;
  return requestJson<{ address: string; balance: number }>(`/wallet/balance?${query}`);
}

export async function fetchWalletBalancesV1(token: string, address: string) {
  return requestJson<{ address: string; assets: { asset_id: string; name?: string }[]; balances: { asset_id: string; balance: number }[] }>(
    `/wallet/v1/balances?address=${encodeURIComponent(address)}`,
    { token }
  );
}

export async function fetchWalletTransfersV1(token: string, address: string, limit: number = 50, offset: number = 0) {
  return requestJson<{ address: string; transfers: any[]; limit: number; offset: number }>(
    `/wallet/v1/transfers?address=${encodeURIComponent(address)}&limit=${limit}&offset=${offset}`,
    { token }
  );
}

export async function transferWallet(
  token: string,
  seed: number,
  runId: string,
  fromAddress: string,
  toAddress: string,
  amount: number,
  assetId: string = "NYXT"
) {
  const body = {
    seed,
    run_id: runId,
    payload: {
      from_address: fromAddress,
      to_address: toAddress,
      amount,
      asset_id: assetId,
    },
  };
  return requestJson<Record<string, unknown>>("/wallet/v1/transfer", {
    method: "POST",
    token,
    body,
    retry: false,
  });
}

export async function faucetWallet(
  token: string,
  seed: number,
  runId: string,
  address: string,
  amount: number = 1000,
  assetId: string = "NYXT"
) {
  const body = {
    seed,
    run_id: runId,
    payload: { address, amount, asset_id: assetId },
  };
  return requestJson<Record<string, unknown>>("/wallet/v1/faucet", {
    method: "POST",
    token,
    body,
    retry: false,
  });
}

export async function placeOrder(
  token: string,
  seed: number,
  runId: string,
  ownerAddress: string,
  side: "BUY" | "SELL",
  amount: number,
  price: number,
  assetIn: string,
  assetOut: string
) {
  const payload = {
    seed,
    run_id: runId,
    module: "exchange",
    action: "place_order",
    payload: {
      owner_address: ownerAddress,
      side,
      amount,
      price,
      asset_in: assetIn,
      asset_out: assetOut,
    },
  };
  return requestJson<Record<string, unknown>>("/run", {
    method: "POST",
    token,
    body: payload,
    retry: false,
  });
}

export async function cancelOrder(token: string, seed: number, runId: string, orderId: string) {
  const payload = {
    seed,
    run_id: runId,
    module: "exchange",
    action: "cancel_order",
    payload: { order_id: orderId },
  };
  return requestJson<Record<string, unknown>>("/run", {
    method: "POST",
    token,
    body: payload,
    retry: false,
  });
}

export async function fetchOrderBook(limit: number = 50, offset: number = 0) {
  return requestJson<Record<string, unknown>>(`/exchange/orderbook?limit=${limit}&offset=${offset}`);
}

export async function fetchMyOrdersV1(token: string, status: string = "open", limit: number = 50, offset: number = 0) {
  const qs = new URLSearchParams();
  qs.set("status", status);
  qs.set("limit", String(limit));
  qs.set("offset", String(offset));
  return requestJson<{ orders: Record<string, unknown>[]; limit: number; offset: number; status: string }>(
    `/exchange/v1/my_orders?${qs.toString()}`,
    { token }
  );
}

export async function fetchMyTradesV1(token: string, limit: number = 50, offset: number = 0) {
  const qs = new URLSearchParams();
  qs.set("limit", String(limit));
  qs.set("offset", String(offset));
  return requestJson<{ trades: Record<string, unknown>[]; limit: number; offset: number }>(
    `/exchange/v1/my_trades?${qs.toString()}`,
    { token }
  );
}

export async function fetchOrders(limit: number = 100, offset: number = 0) {
  return requestJson<{ orders: Record<string, unknown>[] }>(`/exchange/orders?limit=${limit}&offset=${offset}`);
}

export async function fetchTrades(limit: number = 100, offset: number = 0) {
  return requestJson<{ trades: Record<string, unknown>[] }>(`/exchange/trades?limit=${limit}&offset=${offset}`);
}

export async function listChatRooms(accessToken: string, limit: number = 50, offset: number = 0) {
  return requestJson<{ rooms: Record<string, unknown>[] }>(`/chat/v1/rooms?limit=${limit}&offset=${offset}`, {
    token: accessToken,
  });
}

export async function createChatRoom(accessToken: string, name: string, isPublic: boolean = true) {
  return requestJson<Record<string, unknown>>("/chat/v1/rooms", {
    method: "POST",
    token: accessToken,
    body: { name, is_public: isPublic },
    retry: false,
  });
}

export async function listChatMessages(accessToken: string, roomId: string, after?: number, limit: number = 50) {
  const qs = new URLSearchParams();
  if (after !== undefined) qs.set("after", String(after));
  qs.set("limit", String(limit));
  return requestJson<{ messages: Record<string, unknown>[] }>(
    `/chat/v1/rooms/${encodeURIComponent(roomId)}/messages?${qs.toString()}`,
    { token: accessToken }
  );
}

export async function upsertE2eeIdentity(accessToken: string, publicJwk: JsonWebKey) {
  return requestJson<{ account_id: string; public_jwk: JsonWebKey; updated_at: number }>("/portal/v1/e2ee/identity", {
    method: "POST",
    token: accessToken,
    body: { public_jwk: publicJwk },
    retry: false,
  });
}

export async function searchPortalAccounts(accessToken: string, q: string, limit: number = 20) {
  const qs = new URLSearchParams();
  qs.set("q", q);
  qs.set("limit", String(limit));
  return requestJson<{ accounts: { account_id: string; handle: string; public_jwk: JsonWebKey | null }[] }>(
    `/portal/v1/accounts/search?${qs.toString()}`,
    { token: accessToken }
  );
}

export async function fetchChatConversations(accessToken: string, limit: number = 50, offset: number = 0) {
  return requestJson<{ conversations: Record<string, unknown>[]; limit: number; offset: number }>(
    `/chat/v1/conversations?limit=${limit}&offset=${offset}`,
    { token: accessToken }
  );
}

export async function fetchChatMessages(accessToken: string, channel: string, limit: number = 50, offset: number = 0) {
  const qs = new URLSearchParams();
  qs.set("channel", channel);
  qs.set("limit", String(limit));
  qs.set("offset", String(offset));
  return requestJson<{ channel: string; messages: Record<string, unknown>[]; limit: number; offset: number }>(
    `/chat/messages?${qs.toString()}`,
    { token: accessToken }
  );
}

type StoredE2eeIdentity = { publicJwk: JsonWebKey; privateJwk: JsonWebKey; createdAt: number };

const E2EE_IDENTITY_KEY = "nyx_e2ee_identity_v1";

function base64ToBytes(b64: string): Uint8Array {
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

async function loadOrCreateE2eeIdentity(): Promise<{ publicJwk: JsonWebKey; privateKey: CryptoKey }> {
  try {
    const raw = localStorage.getItem(E2EE_IDENTITY_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as StoredE2eeIdentity;
      if (parsed?.publicJwk && parsed?.privateJwk) {
        const privateKey = await window.crypto.subtle.importKey(
          "jwk",
          parsed.privateJwk,
          { name: "ECDH", namedCurve: "P-256" },
          false,
          ["deriveKey", "deriveBits"]
        );
        return { publicJwk: parsed.publicJwk, privateKey };
      }
    }
  } catch {
    // ignore
  }

  const keyPair = await window.crypto.subtle.generateKey({ name: "ECDH", namedCurve: "P-256" }, true, [
    "deriveKey",
    "deriveBits",
  ]);
  const publicJwk = (await window.crypto.subtle.exportKey("jwk", keyPair.publicKey)) as JsonWebKey;
  const privateJwk = (await window.crypto.subtle.exportKey("jwk", keyPair.privateKey)) as JsonWebKey;
  const record: StoredE2eeIdentity = { publicJwk, privateJwk, createdAt: Date.now() };
  try {
    localStorage.setItem(E2EE_IDENTITY_KEY, JSON.stringify(record));
  } catch {
    // ignore
  }
  return { publicJwk, privateKey: keyPair.privateKey };
}

async function deriveDmKey(otherPublicJwk: JsonWebKey): Promise<CryptoKey> {
  const identity = await loadOrCreateE2eeIdentity();
  const otherPublicKey = await window.crypto.subtle.importKey(
    "jwk",
    otherPublicJwk,
    { name: "ECDH", namedCurve: "P-256" },
    false,
    []
  );
  return window.crypto.subtle.deriveKey(
    { name: "ECDH", public: otherPublicKey },
    identity.privateKey,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"]
  );
}

export async function ensureE2eeIdentity(accessToken: string): Promise<JsonWebKey> {
  const identity = await loadOrCreateE2eeIdentity();
  await upsertE2eeIdentity(accessToken, identity.publicJwk);
  return identity.publicJwk;
}

export async function encryptMessage(otherPublicJwk: JsonWebKey, plaintext: string): Promise<string> {
  const key = await deriveDmKey(otherPublicJwk);
  const iv = window.crypto.getRandomValues(new Uint8Array(12));
  const encrypted = await window.crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, new TextEncoder().encode(plaintext));
  return JSON.stringify({
    v: 1,
    alg: "ECDH-P256/AES-256-GCM",
    iv: bytesToBase64(iv),
    ciphertext: bytesToBase64(new Uint8Array(encrypted)),
  });
}

export async function decryptMessage(otherPublicJwk: JsonWebKey, body: string): Promise<string> {
  try {
    const parsed = JSON.parse(body) as any;
    if (!parsed || typeof parsed !== "object") return "[Unsupported message]";
    const iv = base64ToBytes(String(parsed.iv || ""));
    const ciphertext = base64ToBytes(String(parsed.ciphertext || ""));
    const key = await deriveDmKey(otherPublicJwk);
    const decrypted = await window.crypto.subtle.decrypt({ name: "AES-GCM", iv }, key, ciphertext);
    return new TextDecoder().decode(decrypted);
  } catch {
    return "[Decryption Failed]";
  }
}

export async function sendChatMessage(
  accessToken: string,
  seed: number,
  runId: string,
  channel: string,
  ciphertext: string
) {
  const payload = {
    seed,
    run_id: runId,
    module: "chat",
    action: "message_event",
    payload: { channel, message: ciphertext },
  };
  return requestJson<Record<string, unknown>>("/run", {
    method: "POST",
    token: accessToken,
    body: payload,
    retry: false,
  });
}

export async function listMarketplaceListings(limit: number = 50, offset: number = 0) {
  const qs = new URLSearchParams();
  qs.set("limit", String(limit));
  qs.set("offset", String(offset));
  return requestJson<{ listings: Record<string, unknown>[]; limit: number; offset: number }>(
    `/marketplace/listings?${qs.toString()}`
  );
}

export async function searchMarketplaceListings(q: string, limit: number = 50, offset: number = 0) {
  const qs = new URLSearchParams();
  qs.set("q", q);
  qs.set("limit", String(limit));
  qs.set("offset", String(offset));
  return requestJson<{ listings: Record<string, unknown>[]; limit: number; offset: number; q: string }>(
    `/marketplace/listings/search?${qs.toString()}`
  );
}

export async function fetchMyPurchasesV1(token: string, limit: number = 50, offset: number = 0) {
  const qs = new URLSearchParams();
  qs.set("limit", String(limit));
  qs.set("offset", String(offset));
  return requestJson<{ purchases: Record<string, unknown>[]; limit: number; offset: number }>(
    `/marketplace/v1/my_purchases?${qs.toString()}`,
    { token }
  );
}

export async function listMarketplacePurchases(listingId?: string, limit: number = 100, offset: number = 0) {
  const qs = new URLSearchParams();
  if (listingId) qs.set("listing_id", listingId);
  qs.set("limit", String(limit));
  qs.set("offset", String(offset));
  return requestJson<{ purchases: Record<string, unknown>[] }>(`/marketplace/purchases?${qs.toString()}`);
}

export async function publishListing(
  token: string,
  seed: number,
  runId: string,
  publisherId: string,
  sku: string,
  title: string,
  price: number
) {
  const payload = {
    seed,
    run_id: runId,
    module: "marketplace",
    action: "listing_publish",
    payload: { publisher_id: publisherId, sku, title, price },
  };
  return requestJson<Record<string, unknown>>("/run", {
    method: "POST",
    token,
    body: payload,
    retry: false,
  });
}

export async function purchaseMarketplace(token: string, seed: number, runId: string, buyerId: string, listingId: string, qty: number) {
  const payload = {
    seed,
    run_id: runId,
    module: "marketplace",
    action: "purchase_listing",
    payload: { buyer_id: buyerId, listing_id: listingId, qty },
  };
  return requestJson<Record<string, unknown>>("/run", {
    method: "POST",
    token,
    body: payload,
    retry: false,
  });
}

export async function fetchDiscoveryFeed() {
  return requestJson<{ feed: { type: string; data: any }[] }>("/discovery/feed");
}

export interface AirdropTaskV1 {
  task_id: string;
  title: string;
  description: string;
  reward: number;
  completed: boolean;
  completion_run_id: string | null;
  claimed: boolean;
  claim_run_id: string | null;
  claimable: boolean;
}

export async function fetchAirdropTasksV1(token: string) {
  return requestJson<{ account_id: string; tasks: AirdropTaskV1[] }>("/wallet/v1/airdrop/tasks", { token });
}

export async function claimAirdropV1(token: string, seed: number, runId: string, taskId: string) {
  const payload = {
    seed,
    run_id: runId,
    payload: { task_id: taskId },
  };
  return requestJson<Record<string, unknown>>("/wallet/v1/airdrop/claim", {
    method: "POST",
    token,
    body: payload,
    retry: false,
  });
}

export async function listEntertainmentItems(limit: number = 100, offset: number = 0) {
  return requestJson<{ items: Record<string, unknown>[] }>(`/entertainment/items?limit=${limit}&offset=${offset}`);
}

export async function listEntertainmentEvents(itemId?: string, limit: number = 100, offset: number = 0) {
  const qs = new URLSearchParams();
  if (itemId) qs.set("item_id", itemId);
  qs.set("limit", String(limit));
  qs.set("offset", String(offset));
  return requestJson<{ events: Record<string, unknown>[] }>(`/entertainment/events?${qs.toString()}`);
}

export async function postEntertainmentStep(seed: number, runId: string, payload: Record<string, unknown>) {
  return requestJson<Record<string, unknown>>("/entertainment/step", {
    method: "POST",
    body: { seed, run_id: runId, payload },
    retry: false,
  });
}
