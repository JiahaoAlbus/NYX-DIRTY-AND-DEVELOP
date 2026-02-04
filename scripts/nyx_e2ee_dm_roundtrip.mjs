import { webcrypto } from "node:crypto";

if (!globalThis.crypto) {
  globalThis.crypto = webcrypto;
}

const crypto = globalThis.crypto;

function mustEnv(name) {
  const value = process.env[name];
  if (!value) throw new Error(`Missing env ${name}`);
  return value;
}

function base64(bytes) {
  return Buffer.from(bytes).toString("base64");
}

function base64ToBytes(value) {
  return new Uint8Array(Buffer.from(value, "base64"));
}

function urlJoin(baseUrl, path) {
  return `${baseUrl.replace(/\/+$/, "")}${path}`;
}

async function requestJson(method, baseUrl, path, token, body) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(urlJoin(baseUrl, path), {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await res.text();
  let payload = {};
  if (text.trim()) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = { error: { message: text } };
    }
  }
  if (!res.ok) {
    const message =
      payload?.error?.message ??
      payload?.error ??
      `HTTP ${res.status}`;
    const code = payload?.error?.code;
    const details = payload?.error?.details;
    const extra = [];
    if (code) extra.push(code);
    if (details && typeof details === "object") extra.push(JSON.stringify(details));
    throw new Error(extra.length ? `${message} (${extra.join(" ")})` : message);
  }
  return payload;
}

async function getJson(baseUrl, path, token) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(urlJoin(baseUrl, path), { headers });
  const text = await res.text();
  let payload = {};
  if (text.trim()) payload = JSON.parse(text);
  if (!res.ok) {
    const message =
      payload?.error?.message ??
      payload?.error ??
      `HTTP ${res.status}`;
    throw new Error(message);
  }
  return payload;
}

async function importP256PublicKey(jwk) {
  return crypto.subtle.importKey(
    "jwk",
    jwk,
    { name: "ECDH", namedCurve: "P-256" },
    false,
    []
  );
}

async function deriveDmKey(privateKey, otherPublicJwk) {
  const otherPublicKey = await importP256PublicKey(otherPublicJwk);
  return crypto.subtle.deriveKey(
    { name: "ECDH", public: otherPublicKey },
    privateKey,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"]
  );
}

function dmChannel(a, b) {
  const [x, y] = [a, b].sort();
  return `dm/${x}/${y}`;
}

async function main() {
  const baseUrl = mustEnv("NYX_BASE_URL");
  const tokenA = mustEnv("NYX_TOKEN_A");
  const tokenB = mustEnv("NYX_TOKEN_B");
  const accountA = mustEnv("NYX_ACCOUNT_A");
  const accountB = mustEnv("NYX_ACCOUNT_B");
  const seed = Number(mustEnv("NYX_SEED"));
  const runId = mustEnv("NYX_CHAT_RUN_ID");
  const plaintext = mustEnv("NYX_CHAT_PLAINTEXT");

  const channel = dmChannel(accountA, accountB);

  const keyPairA = await crypto.subtle.generateKey(
    { name: "ECDH", namedCurve: "P-256" },
    true,
    ["deriveKey", "deriveBits"]
  );
  const keyPairB = await crypto.subtle.generateKey(
    { name: "ECDH", namedCurve: "P-256" },
    true,
    ["deriveKey", "deriveBits"]
  );
  const publicJwkA = await crypto.subtle.exportKey("jwk", keyPairA.publicKey);
  const publicJwkB = await crypto.subtle.exportKey("jwk", keyPairB.publicKey);

  await requestJson("POST", baseUrl, "/portal/v1/e2ee/identity", tokenA, { public_jwk: publicJwkA });
  await requestJson("POST", baseUrl, "/portal/v1/e2ee/identity", tokenB, { public_jwk: publicJwkB });

  const fetchedA = await getJson(baseUrl, `/portal/v1/accounts/by_id?account_id=${encodeURIComponent(accountA)}`, tokenB);
  const fetchedB = await getJson(baseUrl, `/portal/v1/accounts/by_id?account_id=${encodeURIComponent(accountB)}`, tokenA);
  const storedPublicA = fetchedA?.account?.public_jwk ?? publicJwkA;
  const storedPublicB = fetchedB?.account?.public_jwk ?? publicJwkB;

  const keyAtoB = await deriveDmKey(keyPairA.privateKey, storedPublicB);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encrypted = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    keyAtoB,
    new TextEncoder().encode(plaintext)
  );
  const messageBody = JSON.stringify({
    v: 1,
    alg: "ECDH-P256/AES-256-GCM",
    iv: base64(iv),
    ciphertext: base64(new Uint8Array(encrypted)),
  });

  const sendResponse = await requestJson("POST", baseUrl, "/run", tokenA, {
    seed,
    run_id: runId,
    module: "chat",
    action: "message_event",
    payload: { channel, message: messageBody },
  });

  const messagesResponse = await getJson(
    baseUrl,
    `/chat/messages?channel=${encodeURIComponent(channel)}&limit=50&offset=0`,
    tokenB
  );
  const messages = Array.isArray(messagesResponse?.messages) ? messagesResponse.messages : [];
  const row = messages.find((m) => m?.run_id === runId);
  if (!row) {
    throw new Error(`message not found for run_id=${runId}`);
  }

  const keyBtoA = await deriveDmKey(keyPairB.privateKey, storedPublicA);
  const parsed = JSON.parse(String(row.body || "{}"));
  const decodedIv = base64ToBytes(String(parsed.iv || ""));
  const decodedCiphertext = base64ToBytes(String(parsed.ciphertext || ""));
  const decrypted = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv: decodedIv },
    keyBtoA,
    decodedCiphertext
  );
  const decryptedText = new TextDecoder().decode(decrypted);
  const ok = decryptedText === plaintext;

  const output = {
    ok,
    channel,
    run_id: runId,
    plaintext,
    decrypted: decryptedText,
    send_response: {
      run_id: sendResponse?.run_id,
      status: sendResponse?.status,
      state_hash: sendResponse?.state_hash,
      receipt_hashes: sendResponse?.receipt_hashes,
      replay_ok: sendResponse?.replay_ok,
      fee_total: sendResponse?.fee_total,
      treasury_address: sendResponse?.treasury_address,
    },
    stored_public_jwk_a: storedPublicA,
    stored_public_jwk_b: storedPublicB,
  };

  process.stdout.write(JSON.stringify(output, null, 2));
  if (!ok) process.exit(2);
}

main().catch((err) => {
  process.stderr.write(`${err?.stack ?? err}\n`);
  process.exit(1);
});
