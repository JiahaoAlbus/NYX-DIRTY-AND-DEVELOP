import React, { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Eye, EyeOff, Globe, Key, Lock, RefreshCw, Send, Shield } from "lucide-react";
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
import { useI18n } from "../i18n";

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
    throw new Error("WEB_CRYPTO_UNAVAILABLE");
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
  const { t } = useI18n();
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
      setAllowlistError(t("common.backendUnavailable"));
      return;
    }
    setAllowlistLoading(true);
    setAllowlistError("");
    try {
      const payload = await fetchWeb2Allowlist();
      setAllowlist(payload.allowlist || []);
    } catch (err) {
      const message = err instanceof ApiError ? `${err.code}: ${err.message}` : (err as Error).message;
      setAllowlistError(t("web2.allowlistFailed", { message }));
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
      setHistoryError(t("web2.historyFailed", { message }));
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
      setStatus(t("common.backendUnavailable"));
      return;
    }
    if (!session?.access_token) {
      setStatus(t("common.signInRequired"));
      return;
    }
    const trimmedUrl = url.trim();
    if (!trimmedUrl) {
      setStatus(t("common.urlRequired"));
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
        const msg = (err as Error).message;
        setStatus(msg === "WEB_CRYPTO_UNAVAILABLE" ? t("web2.cryptoUnavailable") : msg);
        return;
      }
    }

    const bodyText = body.trim();
    if (method === "GET" && bodyText) {
      setStatus(t("web2.bodyNotAllowed"));
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
      setStatus(t("web2.requestFailed", { message }));
    } finally {
      setSending(false);
    }
  };

  const hintRows = allowlist.map((entry) => (
    <button
      key={entry.id}
      onClick={() => setUrl(entry.base_url)}
      className="px-3 py-2 rounded-xl text-xs font-bold border border-black/5 dark:border-white/10 bg-surface-light dark:bg-surface-dark/50 hover:border-primary/40 transition-all"
      title={t("web2.allowlistedTitle", { url: entry.base_url })}
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
        <h2 className="text-2xl font-bold">{t("web2.title")}</h2>
        <p className="text-sm text-text-subtle mt-2">{t("web2.subtitle")}</p>
      </div>

      <div className="flex flex-col gap-4">
        <div className="p-6 rounded-3xl glass bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5 flex flex-col gap-6">
          <div className="flex items-center justify-between">
            <div className="text-xs font-bold uppercase text-text-subtle">{t("web2.allowlist")}</div>
            <button
              onClick={loadAllowlist}
              disabled={allowlistLoading}
              className="flex items-center gap-2 text-xs font-bold text-primary"
            >
              <RefreshCw size={14} className={allowlistLoading ? "animate-spin" : ""} />
              {t("common.refresh")}
            </button>
          </div>
          {allowlist.length === 0 ? (
            <div className="text-xs text-text-subtle">
              {allowlistLoading ? t("web2.loadingAllowlist") : allowlistError || t("web2.noAllowlist")}
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">{hintRows}</div>
          )}

          <div className="flex flex-col gap-2">
            <label className="text-[10px] text-text-subtle uppercase px-1">{t("web2.targetUrl")}</label>
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
              <label className="text-[10px] text-text-subtle uppercase px-1">{t("web2.method")}</label>
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
              <label className="text-[10px] text-text-subtle uppercase px-1">{t("web2.body")}</label>
              <input
                className="bg-transparent flex-1 outline-none text-sm font-mono px-4 py-3 bg-background-light dark:bg-background-dark rounded-2xl border border-black/5 dark:border-white/5"
                value={body}
                onChange={(e) => setBody(e.target.value)}
                disabled={method === "GET"}
              />
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-[10px] text-text-subtle uppercase px-1">{t("web2.sealedKey")}</label>
            <div className="flex items-center gap-3 px-4 py-3 bg-background-light dark:bg-background-dark rounded-2xl border border-black/5 dark:border-white/5">
              <Key size={18} className="text-text-subtle" />
              <input
                type={showSecret ? "text" : "password"}
                className="bg-transparent flex-1 outline-none text-sm font-mono"
                value={secret}
                onChange={(e) => setSecret(e.target.value)}
              />
              <button
                onClick={() => setShowSecret(!showSecret)}
                className="text-text-subtle hover:text-text-main dark:text-white transition-colors"
              >
                {showSecret ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-orange-500/5 border border-orange-500/10 flex gap-3 items-start">
            <AlertTriangle size={16} className="text-orange-500 shrink-0 mt-0.5" />
            <div className="text-[10px] text-text-subtle leading-relaxed">{t("web2.sealedNote")}</div>
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
            {t("web2.send")}
          </button>
        </div>

        {lastResponse && (
          <div className="p-5 rounded-3xl bg-black/5 dark:bg-white/5 border border-white/10 text-xs">
            <div className="font-bold">{t("web2.latestResponse")}</div>
            <div className="mt-2 grid grid-cols-1 gap-1 font-mono text-[10px] text-text-subtle break-all">
              <div>
                {t("common.runId")}: {lastResponse.run_id}
              </div>
              <div>
                {t("common.status")}: {lastResponse.response_status}
              </div>
              <div>
                {t("web2.requestHash")}: {lastResponse.request_hash}
              </div>
              <div>
                {t("web2.responseHash")}: {lastResponse.response_hash}
              </div>
              <div>
                {t("activity.feeTotal")} {lastResponse.fee_total}
              </div>
              {lastResponse.treasury_address && (
                <div>
                  {t("activity.treasury")} {lastResponse.treasury_address}
                </div>
              )}
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
              {t("activity.openEvidence")}
            </button>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-3xl glass bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5 flex flex-col items-center gap-2 text-center">
            <Shield size={24} className="text-blue-500" />
            <div className="text-[10px] font-bold">{t("web2.allowlistGate")}</div>
          </div>
          <div className="p-4 rounded-3xl glass bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5 flex flex-col items-center gap-2 text-center">
            <Lock size={24} className="text-purple-500" />
            <div className="text-[10px] font-bold">{t("web2.ciphertextOnly")}</div>
          </div>
        </div>

        <div className="p-6 rounded-3xl glass bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="text-xs font-bold uppercase text-text-subtle">{t("web2.recentRequests")}</div>
            <button onClick={() => loadHistory(true)} className="text-xs font-bold text-primary">
              {t("common.refresh")}
            </button>
          </div>
          {history.length === 0 ? (
            <div className="text-xs text-text-subtle">
              {historyLoading ? t("web2.loadingHistory") : historyError || t("web2.noRequests")}
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
                  <div className="text-[10px] text-text-subtle">
                    {t("common.runId")}: {row.run_id}
                  </div>
                </div>
              ))}
              {historyHasMore && (
                <button
                  onClick={() => loadHistory()}
                  disabled={historyLoading}
                  className="text-xs font-bold text-primary underline"
                >
                  {historyLoading ? t("common.loading") : t("common.loadMore")}
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
