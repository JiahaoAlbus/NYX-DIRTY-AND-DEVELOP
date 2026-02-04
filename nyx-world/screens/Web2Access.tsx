import React, { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Eye,
  EyeOff,
  Globe,
  Key,
  Lock,
  RefreshCw,
  Send,
  Shield,
} from "lucide-react";
import {
  allocateRunId,
  ApiError,
  executeWeb2GuardRequest,
  fetchWeb2Allowlist,
  fetchWeb2Requests,
  parseSeed,
  PortalSession,
} from "../api";
import { bytesToBase64 } from "../utils";
import type { Web2AllowlistEntry, Web2GuardRequestRow, Web2GuardResponse } from "../types";
import { Screen } from "../types";

interface Web2AccessProps {
  seed: string;
  runId: string;
  backendOnline: boolean;
  session: PortalSession | null;
  onNavigate: (screen: Screen) => void;
}

const DEFAULT_URL = "https://api.coingecko.com/api/v3/ping";

const sealSecret = async (secret: string, seed: string): Promise<string> => {
  if (!window.crypto?.subtle) {
    throw new Error("Web Crypto unavailable.");
  }
  const enc = new TextEncoder();
  const seedBytes = enc.encode(seed);
  const digest = await window.crypto.subtle.digest("SHA-256", seedBytes);
  const key = await window.crypto.subtle.importKey("raw", digest, { name: "AES-GCM" }, false, ["encrypt"]);
  const iv = window.crypto.getRandomValues(new Uint8Array(12));
  const ciphertext = await window.crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, enc.encode(secret));
  const combined = new Uint8Array(iv.length + ciphertext.byteLength);
  combined.set(iv, 0);
  combined.set(new Uint8Array(ciphertext), iv.length);
  return bytesToBase64(combined);
};

export const Web2Access: React.FC<Web2AccessProps> = ({ seed, runId, backendOnline, session, onNavigate }) => {
  const [allowlist, setAllowlist] = useState<Web2AllowlistEntry[]>([]);
  const [allowlistLoading, setAllowlistLoading] = useState(false);
  const [allowlistError, setAllowlistError] = useState<string>("");

  const [url, setUrl] = useState(DEFAULT_URL);
  const [method, setMethod] = useState<"GET" | "POST">("GET");
  const [body, setBody] = useState("");
  const [secret, setSecret] = useState("");
  const [showSecret, setShowSecret] = useState(false);

  const [sending, setSending] = useState(false);
  const [status, setStatus] = useState<string>("");
  const [lastResponse, setLastResponse] = useState<Web2GuardResponse | null>(null);

  const [history, setHistory] = useState<Web2GuardRequestRow[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [historyOffset, setHistoryOffset] = useState(0);
  const [historyHasMore, setHistoryHasMore] = useState(true);
  const historyLimit = 10;

  const baseRunId = useMemo(() => (runId || "").trim() || "web2-guard", [runId]);

  const loadAllowlist = async () => {
    if (!backendOnline) {
      setAllowlistError("Backend unavailable.");
      return;
    }
    setAllowlistLoading(true);
    setAllowlistError("");
    try {
      const payload = await fetchWeb2Allowlist();
      setAllowlist(payload.allowlist || []);
    } catch (err) {
      const message = err instanceof ApiError ? `${err.code}: ${err.message}` : (err as Error).message;
      setAllowlistError(`Failed to load allowlist: ${message}`);
    } finally {
      setAllowlistLoading(false);
    }
  };

  const loadHistory = async (reset?: boolean) => {
    if (!backendOnline || !session?.access_token) return;
    setHistoryLoading(true);
    setHistoryError("");
    try {
      const nextOffset = reset ? 0 : historyOffset;
      const payload = await fetchWeb2Requests(session.access_token, historyLimit, nextOffset);
      const rows = payload.requests || [];
      if (reset) {
        setHistory(rows);
      } else {
        setHistory((prev) => [...prev, ...rows]);
      }
      setHistoryHasMore(rows.length === historyLimit);
      setHistoryOffset(nextOffset + rows.length);
    } catch (err) {
      const message = err instanceof ApiError ? `${err.code}: ${err.message}` : (err as Error).message;
      setHistoryError(`Failed to load history: ${message}`);
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    loadAllowlist();
    loadHistory(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [backendOnline, session?.access_token]);

  const handleSend = async () => {
    if (!backendOnline) {
      setStatus("Backend unavailable.");
      return;
    }
    if (!session?.access_token) {
      setStatus("Sign in required.");
      return;
    }
    const trimmedUrl = url.trim();
    if (!trimmedUrl) {
      setStatus("URL required.");
      return;
    }

    let seedValue = 0;
    try {
      seedValue = parseSeed(seed);
    } catch (err) {
      setStatus((err as Error).message);
      return;
    }

    let sealed: string | undefined = undefined;
    if (secret.trim()) {
      try {
        sealed = await sealSecret(secret.trim(), seed);
      } catch (err) {
        setStatus((err as Error).message);
        return;
      }
    }

    const bodyText = body.trim();
    if (method === "GET" && bodyText) {
      setStatus("Body not allowed for GET.");
      return;
    }

    const runIdValue = allocateRunId(baseRunId, "request");
    setSending(true);
    setStatus("");
    setLastResponse(null);
    try {
      const result = await executeWeb2GuardRequest(session.access_token, seedValue, runIdValue, {
        url: trimmedUrl,
        method,
        body: bodyText ? bodyText : undefined,
        sealed_request: sealed,
      });
      setLastResponse(result);
      await loadHistory(true);
    } catch (err) {
      const message = err instanceof ApiError ? `${err.code}: ${err.message}` : (err as Error).message;
      setStatus(`Request failed: ${message}`);
    } finally {
      setSending(false);
    }
  };

  const hintRows = allowlist.map((entry) => (
    <button
      key={entry.id}
      onClick={() => setUrl(entry.base_url)}
      className="px-3 py-2 rounded-xl text-xs font-bold border border-black/5 dark:border-white/10 bg-surface-light dark:bg-surface-dark/50 hover:border-primary/40 transition-all"
      title={`Allowlisted: ${entry.base_url}`}
    >
      {entry.label}
    </button>
  ));

  return (
    <div className="flex flex-col gap-6 text-text-main dark:text-white pb-24">
      <div className="p-8 rounded-3xl bg-gradient-to-br from-blue-600/20 to-purple-600/20 glass border border-white/10 flex flex-col items-center text-center">
        <div className="size-20 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-500 mb-4 shadow-2xl border border-blue-500/30">
          <Globe size={40} />
        </div>
        <h2 className="text-2xl font-bold">Web2 Guard</h2>
        <p className="text-sm text-text-subtle mt-2">Allowlisted Web2 requests with deterministic evidence + fees</p>
      </div>

      <div className="flex flex-col gap-4">
        <div className="p-6 rounded-3xl glass bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5 flex flex-col gap-6">
          <div className="flex items-center justify-between">
            <div className="text-xs font-bold uppercase text-text-subtle">Allowlist</div>
            <button
              onClick={loadAllowlist}
              disabled={allowlistLoading}
              className="flex items-center gap-2 text-xs font-bold text-primary"
            >
              <RefreshCw size={14} className={allowlistLoading ? "animate-spin" : ""} />
              Refresh
            </button>
          </div>
          {allowlist.length === 0 ? (
            <div className="text-xs text-text-subtle">
              {allowlistLoading ? "Loading allowlist…" : allowlistError || "No allowlisted endpoints yet."}
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">{hintRows}</div>
          )}

          <div className="flex flex-col gap-2">
            <label className="text-[10px] text-text-subtle uppercase px-1">Target URL</label>
            <div className="flex items-center gap-3 px-4 py-3 bg-background-light dark:bg-background-dark rounded-2xl border border-black/5 dark:border-white/5">
              <Globe size={18} className="text-text-subtle" />
              <input
                className="bg-transparent flex-1 outline-none text-sm font-mono"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-2">
              <label className="text-[10px] text-text-subtle uppercase px-1">Method</label>
              <select
                className="h-11 rounded-2xl bg-background-light dark:bg-background-dark border border-black/5 dark:border-white/5 px-4 text-sm outline-none"
                value={method}
                onChange={(e) => setMethod(e.target.value as "GET" | "POST")}
              >
                <option value="GET">GET</option>
                <option value="POST">POST</option>
              </select>
            </div>
            <div className="flex flex-col gap-2">
              <label className="text-[10px] text-text-subtle uppercase px-1">Body</label>
              <input
                className="bg-transparent flex-1 outline-none text-sm font-mono px-4 py-3 bg-background-light dark:bg-background-dark rounded-2xl border border-black/5 dark:border-white/5"
                value={body}
                onChange={(e) => setBody(e.target.value)}
                disabled={method === "GET"}
              />
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-[10px] text-text-subtle uppercase px-1">Sealed Key (Optional)</label>
            <div className="flex items-center gap-3 px-4 py-3 bg-background-light dark:bg-background-dark rounded-2xl border border-black/5 dark:border-white/5">
              <Key size={18} className="text-text-subtle" />
              <input
                type={showSecret ? "text" : "password"}
                className="bg-transparent flex-1 outline-none text-sm font-mono"
                value={secret}
                onChange={(e) => setSecret(e.target.value)}
              />
              <button onClick={() => setShowSecret(!showSecret)} className="text-text-subtle hover:text-text-main dark:text-white transition-colors">
                {showSecret ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-orange-500/5 border border-orange-500/10 flex gap-3 items-start">
            <AlertTriangle size={16} className="text-orange-500 shrink-0 mt-0.5" />
            <div className="text-[10px] text-text-subtle leading-relaxed">
              Secrets are sealed on-device and stored only as ciphertext. Testnet guard forwards only allowlisted public
              endpoints.
            </div>
          </div>

          <button
            onClick={handleSend}
            disabled={sending}
            className="w-full py-4 rounded-2xl bg-blue-500 text-text-main dark:text-white font-bold flex items-center justify-center gap-2 hover:bg-blue-600 transition-all shadow-xl"
          >
            {sending ? (
              <div className="size-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
            ) : (
              <Send size={18} />
            )}
            Send Request
          </button>
        </div>

        {lastResponse && (
          <div className="p-5 rounded-3xl bg-black/5 dark:bg-white/5 border border-white/10 text-xs">
            <div className="font-bold">Latest Response</div>
            <div className="mt-2 grid grid-cols-1 gap-1 font-mono text-[10px] text-text-subtle break-all">
              <div>run_id: {lastResponse.run_id}</div>
              <div>status: {lastResponse.response_status}</div>
              <div>request_hash: {lastResponse.request_hash}</div>
              <div>response_hash: {lastResponse.response_hash}</div>
              <div>fee_total: {lastResponse.fee_total}</div>
              {lastResponse.treasury_address && <div>treasury: {lastResponse.treasury_address}</div>}
            </div>
            {lastResponse.response_preview && (
              <pre className="mt-3 p-3 rounded-2xl bg-black/80 text-green-300 text-[10px] overflow-x-auto max-h-48">
                {lastResponse.response_preview}
              </pre>
            )}
            <button
              onClick={() => onNavigate(Screen.ACTIVITY)}
              className="mt-3 text-xs font-bold text-primary underline"
            >
              Open Evidence Center
            </button>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-3xl glass bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5 flex flex-col items-center gap-2 text-center">
            <Shield size={24} className="text-blue-500" />
            <div className="text-[10px] font-bold">Allowlist Gate</div>
          </div>
          <div className="p-4 rounded-3xl glass bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5 flex flex-col items-center gap-2 text-center">
            <Lock size={24} className="text-purple-500" />
            <div className="text-[10px] font-bold">Ciphertext Only</div>
          </div>
        </div>

        <div className="p-6 rounded-3xl glass bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="text-xs font-bold uppercase text-text-subtle">Recent Requests</div>
            <button onClick={() => loadHistory(true)} className="text-xs font-bold text-primary">
              Refresh
            </button>
          </div>
          {history.length === 0 ? (
            <div className="text-xs text-text-subtle">
              {historyLoading ? "Loading history…" : historyError || "No requests yet."}
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {history.map((row) => (
                <div key={row.request_id} className="p-3 rounded-2xl border border-black/5 dark:border-white/10">
                  <div className="flex items-center justify-between text-[10px] font-mono text-text-subtle">
                    <span>{row.method}</span>
                    <span>{row.response_status}</span>
                  </div>
                  <div className="text-[10px] text-text-subtle break-all">{row.url}</div>
                  <div className="text-[10px] text-text-subtle">run_id: {row.run_id}</div>
                </div>
              ))}
              {historyHasMore && (
                <button
                  onClick={() => loadHistory()}
                  disabled={historyLoading}
                  className="text-xs font-bold text-primary underline"
                >
                  {historyLoading ? "Loading…" : "Load more"}
                </button>
              )}
            </div>
          )}
        </div>

        {status && (
          <div className="fixed bottom-24 left-1/2 -translate-x-1/2 px-6 py-3 rounded-2xl bg-binance-red text-white text-sm font-bold shadow-2xl">
            {status}
          </div>
        )}
      </div>
    </div>
  );
};
