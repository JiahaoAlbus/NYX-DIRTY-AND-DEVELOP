import React, { useEffect, useMemo, useState } from "react";
import {
  allocateRunId,
  ApiError,
  decryptMessage,
  ensureE2eeIdentity,
  encryptMessage,
  fetchChatConversations,
  fetchChatMessages,
  fetchPortalAccountById,
  parseSeed,
  PortalSession,
  searchPortalAccounts,
  sendChatMessage,
} from "../api";
import { Screen } from "../types";

type ConversationRow = {
  channel: string;
  max_rowid: number;
  message_id: string;
  sender_account_id: string;
  run_id: string;
};

type ChatMessageRow = {
  message_id: string;
  channel: string;
  sender_account_id: string;
  body: string;
  run_id: string;
  state_hash?: string;
  receipt_hashes?: string[];
  replay_ok?: boolean;
};

type RunResult = {
  run_id?: string;
  state_hash?: string;
  receipt_hashes?: string[];
  replay_ok?: boolean;
  fee_total?: number;
  treasury_address?: string;
};

type PeerRecord = { account_id: string; handle: string; public_jwk: JsonWebKey };

interface ChatProps {
  seed: string;
  runId: string;
  backendOnline: boolean;
  session: PortalSession | null;
  onNavigate: (screen: Screen) => void;
}

const PAGE_LIMIT = 50;
const PEER_STORAGE_PREFIX = "nyx_e2ee_peer_v1_";

function renderApiError(err: unknown): string {
  if (err instanceof ApiError) {
    const bits = [err.message];
    if (err.code && !err.message.includes(err.code)) bits.push(`(${err.code})`);
    const retryAfter = err.details?.retry_after_seconds;
    if (typeof retryAfter === "number" && Number.isFinite(retryAfter)) {
      bits.push(`retry after ${retryAfter}s`);
    }
    return bits.join(" ");
  }
  return (err as Error)?.message ?? "Unknown error";
}

function formatCompactId(value: string): string {
  const v = (value || "").trim();
  if (v.length <= 18) return v;
  return `${v.slice(0, 10)}…${v.slice(-6)}`;
}

function makeDmChannel(a: string, b: string): string {
  const sorted = [a, b].sort();
  return `dm/${sorted[0]}/${sorted[1]}`;
}

function parseDmPeer(channel: string, me: string): string | null {
  if (!channel.startsWith("dm/")) return null;
  const parts = channel.split("/");
  if (parts.length !== 3) return null;
  const a = parts[1];
  const b = parts[2];
  if (a !== me && b !== me) return null;
  return a === me ? b : a;
}

function loadPeerFromStorage(accountId: string): PeerRecord | null {
  try {
    const raw = localStorage.getItem(`${PEER_STORAGE_PREFIX}${accountId}`);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as PeerRecord;
    if (!parsed?.public_jwk) return null;
    return parsed;
  } catch {
    return null;
  }
}

function savePeerToStorage(peer: PeerRecord) {
  try {
    localStorage.setItem(`${PEER_STORAGE_PREFIX}${peer.account_id}`, JSON.stringify(peer));
  } catch {
    // ignore
  }
}

export const Chat: React.FC<ChatProps> = ({ seed, runId, backendOnline, session, onNavigate }) => {
  const token = session?.access_token ?? "";
  const me = session?.account_id ?? "";

  const [identityError, setIdentityError] = useState("");

  const [conversations, setConversations] = useState<ConversationRow[]>([]);
  const [convLoading, setConvLoading] = useState(false);
  const [convError, setConvError] = useState("");

  const [activeChannel, setActiveChannel] = useState<string>("");
  const activePeerId = useMemo(() => (activeChannel ? parseDmPeer(activeChannel, me) : null), [activeChannel, me]);
  const [activePeer, setActivePeer] = useState<PeerRecord | null>(null);

  const [messages, setMessages] = useState<ChatMessageRow[]>([]);
  const [msgLoading, setMsgLoading] = useState(false);
  const [msgError, setMsgError] = useState("");
  const [msgOffset, setMsgOffset] = useState(0);
  const [msgHasMore, setMsgHasMore] = useState(true);
  const [decrypted, setDecrypted] = useState<Record<string, string>>({});

  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState("");

  const [showNewDm, setShowNewDm] = useState(false);
  const [searchQ, setSearchQ] = useState("");
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [searchResults, setSearchResults] = useState<{ account_id: string; handle: string; public_jwk: JsonWebKey | null }[]>([]);

  const [toast, setToast] = useState("");
  const [lastAction, setLastAction] = useState<RunResult | null>(null);

  const ensureIdentity = async () => {
    if (!backendOnline || !session) return;
    setIdentityError("");
    try {
      await ensureE2eeIdentity(token);
    } catch (err) {
      setIdentityError(renderApiError(err));
    }
  };

  const loadConversations = async () => {
    if (!backendOnline || !session) return;
    setConvLoading(true);
    setConvError("");
    try {
      const payload = await fetchChatConversations(token, 50, 0);
      const list = (payload.conversations as ConversationRow[]) || [];
      setConversations(list);
      if (!activeChannel && list.length > 0) {
        setActiveChannel(String(list[0].channel));
      }
    } catch (err) {
      setConvError(renderApiError(err));
    } finally {
      setConvLoading(false);
    }
  };

  const loadMessages = async (opts?: { reset?: boolean }) => {
    if (!backendOnline || !session || !activeChannel) return;
    setMsgLoading(true);
    setMsgError("");
    try {
      const nextOffset = opts?.reset ? 0 : msgOffset;
      const payload = await fetchChatMessages(token, activeChannel, PAGE_LIMIT, nextOffset);
      const list = (payload.messages as ChatMessageRow[]) || [];
      const ordered = [...list].reverse(); // render oldest->newest
      if (opts?.reset) {
        setMessages(ordered);
        setDecrypted({});
      } else {
        setMessages((prev) => [...ordered, ...prev]);
      }
      setMsgHasMore(list.length === PAGE_LIMIT);
      setMsgOffset(nextOffset + list.length);
    } catch (err) {
      setMsgError(renderApiError(err));
    } finally {
      setMsgLoading(false);
    }
  };

  const resolveActivePeer = async () => {
    if (!activePeerId || !session) {
      setActivePeer(null);
      return;
    }
    const cached = loadPeerFromStorage(activePeerId);
    if (cached) {
      setActivePeer(cached);
      return;
    }
    try {
      const payload = await fetchPortalAccountById(token, activePeerId);
      const account = payload.account;
      if (account.public_jwk) {
        const peer: PeerRecord = { account_id: account.account_id, handle: account.handle, public_jwk: account.public_jwk };
        savePeerToStorage(peer);
        setActivePeer(peer);
      } else {
        setActivePeer(null);
      }
    } catch {
      setActivePeer(null);
    }
  };

  useEffect(() => {
    ensureIdentity();
    loadConversations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [backendOnline, session?.access_token, session?.account_id]);

  useEffect(() => {
    resolveActivePeer();
    loadMessages({ reset: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeChannel]);

  useEffect(() => {
    const run = async () => {
      if (!activePeer || messages.length === 0) return;
      const next: Record<string, string> = { ...decrypted };
      let changed = false;
      for (const msg of messages) {
        if (next[msg.message_id]) continue;
        next[msg.message_id] = await decryptMessage(activePeer.public_jwk, msg.body);
        changed = true;
      }
      if (changed) setDecrypted(next);
    };
    run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages, activePeer?.account_id]);

  const startDm = async (accountId: string, handle: string, publicJwk: JsonWebKey) => {
    if (!session) return;
    const peer: PeerRecord = { account_id: accountId, handle, public_jwk: publicJwk };
    savePeerToStorage(peer);
    setActivePeer(peer);
    const channel = makeDmChannel(me, accountId);
    setActiveChannel(channel);
    setShowNewDm(false);
    setSearchQ("");
    setSearchResults([]);
    await loadConversations();
  };

  const handleSearch = async () => {
    if (!backendOnline || !session) return;
    setSearchError("");
    setSearchLoading(true);
    try {
      const q = searchQ.trim();
      if (!q) {
        setSearchResults([]);
        return;
      }
      const payload = await searchPortalAccounts(token, q, 20);
      setSearchResults(payload.accounts || []);
    } catch (err) {
      setSearchError(renderApiError(err));
    } finally {
      setSearchLoading(false);
    }
  };

  const handleSend = async () => {
    if (!backendOnline || !session || !activeChannel) return;
    setSendError("");
    setToast("");
    setLastAction(null);

    const plain = text.trim();
    if (!plain) return;
    if (!activePeer) {
      setSendError("Peer E2EE key not available. Ask them to open Chat once to register.");
      return;
    }

    let seedInt = 0;
    try {
      seedInt = parseSeed(seed);
    } catch (err) {
      setSendError(renderApiError(err));
      return;
    }

    const run_id = allocateRunId(runId, "chat-message");
    setSending(true);
    try {
      const ciphertext = await encryptMessage(activePeer.public_jwk, plain);
      const result = (await sendChatMessage(token, seedInt, run_id, activeChannel, ciphertext)) as RunResult;
      setLastAction(result);
      setText("");
      await loadMessages({ reset: true });
      setToast(`Sent (run: ${run_id})`);
    } catch (err) {
      setSendError(renderApiError(err));
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex flex-col gap-6 pb-24 text-text-main dark:text-white">
      <div className="flex items-center justify-between px-2">
        <div>
          <div className="text-xl font-black tracking-tight">Chat</div>
          <div className="text-[10px] text-text-subtle uppercase tracking-widest">E2EE only • ciphertext storage</div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowNewDm(true)}
            className="text-[10px] font-bold text-primary uppercase tracking-widest"
            disabled={!session}
            title={!session ? "Sign in required" : "Start a DM"}
          >
            New DM
          </button>
          <button
            onClick={() => onNavigate(Screen.ACTIVITY)}
            className="text-[10px] font-bold text-primary uppercase tracking-widest"
          >
            Evidence
          </button>
        </div>
      </div>

      {identityError && (
        <div className="text-xs text-binance-red bg-binance-red/10 border border-binance-red/20 px-3 py-2 rounded-xl">
          E2EE identity publish failed: {identityError}{" "}
          <button onClick={ensureIdentity} className="underline font-bold">
            Retry
          </button>
        </div>
      )}

      <div className="p-4 rounded-2xl bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5">
        <div className="flex items-center justify-between mb-3">
          <div className="text-xs font-bold text-text-subtle uppercase">Conversations</div>
          <button onClick={loadConversations} className="text-[10px] font-bold text-primary uppercase tracking-widest">
            Refresh
          </button>
        </div>
        {convError && (
          <div className="text-xs text-binance-red bg-binance-red/10 border border-binance-red/20 px-3 py-2 rounded-xl">
            {convError}
          </div>
        )}
        {!convError && conversations.length === 0 && !convLoading && (
          <div className="text-sm text-text-subtle">No conversations yet. Start a DM.</div>
        )}
        <div className="flex gap-2 overflow-x-auto no-scrollbar">
          {conversations.map((c) => {
            const channel = String(c.channel || "");
            const peerId = parseDmPeer(channel, me);
            const label = peerId ? `DM ${formatCompactId(peerId)}` : channel;
            const active = channel === activeChannel;
            return (
              <button
                key={channel}
                onClick={() => setActiveChannel(channel)}
                className={`px-3 py-2 rounded-xl text-xs font-bold whitespace-nowrap border transition-all ${
                  active
                    ? "bg-primary/15 border-primary text-primary"
                    : "bg-surface-light dark:bg-surface-dark border-black/5 dark:border-white/10 text-text-subtle"
                }`}
              >
                {label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Messages */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between px-1">
          <div className="text-xs font-bold text-text-subtle uppercase">
            Channel: <span className="font-mono text-text-subtle">{activeChannel || "—"}</span>
          </div>
          {activeChannel && msgHasMore && (
            <button
              onClick={() => loadMessages()}
              className="text-[10px] font-bold text-primary uppercase tracking-widest"
              disabled={msgLoading}
            >
              Load older
            </button>
          )}
        </div>

        {msgError && (
          <div className="text-xs text-binance-red bg-binance-red/10 border border-binance-red/20 px-3 py-2 rounded-xl">
            {msgError}{" "}
            <button onClick={() => loadMessages({ reset: true })} className="underline font-bold">
              Retry
            </button>
          </div>
        )}

        <div className="p-4 rounded-2xl bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5 min-h-[260px] max-h-[420px] overflow-y-auto no-scrollbar flex flex-col gap-3">
          {activeChannel && messages.length === 0 && !msgLoading && !msgError && (
            <div className="text-sm text-text-subtle">No messages yet.</div>
          )}
          {messages.map((m) => {
            const isMe = m.sender_account_id === me;
            return (
              <div key={m.message_id} className={`flex ${isMe ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[80%] px-3 py-2 rounded-2xl text-sm ${
                    isMe ? "bg-primary text-black rounded-br-none" : "bg-black/5 dark:bg-white/5 rounded-bl-none"
                  }`}
                >
                  <div>{activePeer ? decrypted[m.message_id] || "Decrypting…" : "E2EE key missing"}</div>
                  <div className="mt-1 text-[9px] opacity-60 font-mono break-all">
                    run: {formatCompactId(m.run_id)}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Composer */}
        <div className="p-3 rounded-2xl bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5">
          <div className="flex items-center gap-2">
            <input
              className="flex-1 h-10 rounded-xl bg-surface-light dark:bg-surface-dark border border-black/5 dark:border-white/10 px-3 text-sm outline-none"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={activeChannel ? "Message (encrypted)" : "Select or start a DM"}
              disabled={!activeChannel || sending}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSend();
              }}
            />
            <button
              onClick={handleSend}
              disabled={!activeChannel || sending || !text.trim()}
              className={`px-4 h-10 rounded-xl font-bold text-sm transition-all active:scale-95 ${
                sending ? "bg-surface-light dark:bg-surface-dark text-text-subtle" : "bg-primary text-black"
              }`}
              title={!activeChannel ? "Select a conversation first" : ""}
            >
              {sending ? "…" : "Send"}
            </button>
          </div>
          {sendError && <div className="mt-2 text-xs text-binance-red">{sendError}</div>}
        </div>
      </div>

      {lastAction && (
        <div className="p-4 rounded-2xl bg-black/5 dark:bg-white/5 border border-black/5 dark:border-white/10">
          <div className="text-[10px] font-bold text-text-subtle uppercase mb-1">Last Action</div>
          <div className="text-[10px] font-mono text-text-subtle break-all">run_id: {String(lastAction.run_id ?? "")}</div>
          <div className="text-[10px] font-mono text-text-subtle break-all">
            state_hash: {String(lastAction.state_hash ?? "")}
          </div>
          {lastAction.fee_total !== undefined && (
            <div className="text-[10px] font-mono text-text-subtle break-all">
              fee_total: {String(lastAction.fee_total)} treasury: {String(lastAction.treasury_address ?? "")}
            </div>
          )}
        </div>
      )}

      {showNewDm && (
        <Modal title="Start a DM" onClose={() => setShowNewDm(false)}>
          <div className="flex flex-col gap-3">
            <div className="flex gap-2">
              <input
                className="flex-1 h-10 rounded-xl bg-surface-light dark:bg-surface-dark border border-black/5 dark:border-white/10 px-3 text-sm outline-none"
                value={searchQ}
                onChange={(e) => setSearchQ(e.target.value)}
                placeholder="Search handle prefix (e.g. ali)"
              />
              <button
                onClick={handleSearch}
                className="px-4 h-10 rounded-xl font-bold text-sm bg-primary text-black"
                disabled={searchLoading}
              >
                {searchLoading ? "…" : "Search"}
              </button>
            </div>
            {searchError && <div className="text-xs text-binance-red">{searchError}</div>}
            {searchResults.length === 0 && !searchLoading && (
              <div className="text-sm text-text-subtle">No results.</div>
            )}
            <div className="flex flex-col gap-2 max-h-[260px] overflow-y-auto no-scrollbar">
              {searchResults.map((acc) => {
                const disabled = !acc.public_jwk || acc.account_id === me;
                return (
                  <button
                    key={acc.account_id}
                    onClick={() => acc.public_jwk && startDm(acc.account_id, acc.handle, acc.public_jwk)}
                    disabled={disabled}
                    className={`p-3 rounded-2xl border text-left transition-all ${
                      disabled
                        ? "bg-surface-light dark:bg-surface-dark text-text-subtle border-black/5 dark:border-white/10"
                        : "bg-primary/10 border-primary/30 hover:bg-primary/15"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="font-bold text-sm">@{acc.handle}</div>
                      <div className="text-[10px] text-text-subtle">{formatCompactId(acc.account_id)}</div>
                    </div>
                    <div className="text-[10px] text-text-subtle mt-1">
                      {acc.public_jwk ? "E2EE ready" : "Missing E2EE key (ask them to open Chat once)"}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </Modal>
      )}

      {toast && (
        <div className="fixed bottom-24 left-1/2 -translate-x-1/2 px-4 py-2 rounded-xl bg-primary text-black text-xs font-bold shadow-2xl animate-in slide-in-from-bottom-2">
          {toast}
        </div>
      )}
    </div>
  );
};

const Modal: React.FC<{ title: string; onClose: () => void; children: React.ReactNode }> = ({
  title,
  onClose,
  children,
}) => (
  <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 backdrop-blur-sm px-4 pb-24">
    <div className="w-full max-w-md rounded-3xl bg-background-light dark:bg-background-dark border border-primary/20 shadow-2xl p-5 animate-in slide-in-from-bottom-4">
      <div className="flex items-center justify-between mb-4">
        <div className="text-sm font-bold">{title}</div>
        <button onClick={onClose} className="text-text-subtle hover:text-primary transition-colors">
          <span className="material-symbols-outlined text-[18px]">close</span>
        </button>
      </div>
      {children}
    </div>
  </div>
);
