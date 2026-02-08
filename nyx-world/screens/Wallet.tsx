import React, { useEffect, useMemo, useState } from "react";
import {
  allocateRunId,
  fetchWalletBalancesV1,
  fetchWalletTransfersV1,
  parseSeed,
  PortalSession,
  transferWallet,
} from "../api";
import { Screen } from "../types";

type WalletAsset = { asset_id: string; name?: string };
type WalletBalanceRow = { asset_id: string; balance: number };

interface WalletProps {
  seed: string;
  runId: string;
  backendOnline: boolean;
  session: PortalSession | null;
  onNavigate: (screen: Screen) => void;
}

export const Wallet: React.FC<WalletProps> = ({ seed, runId, backendOnline, session, onNavigate }) => {
  const address = session?.account_id ?? "";
  const token = session?.access_token ?? "";

  const [activeTab, setActiveTab] = useState<"assets" | "activity">("assets");
  const [assets, setAssets] = useState<WalletAsset[]>([]);
  const [balances, setBalances] = useState<WalletBalanceRow[]>([]);
  const [balancesLoading, setBalancesLoading] = useState(false);
  const [balancesError, setBalancesError] = useState<string>("");

  const [transferLoading, setTransferLoading] = useState(false);
  const [transferError, setTransferError] = useState<string>("");
  const [transferTo, setTransferTo] = useState("");
  const [transferAmount, setTransferAmount] = useState("1");
  const [transferAssetId, setTransferAssetId] = useState("NYXT");
  const [showSend, setShowSend] = useState(false);

  const [txLoading, setTxLoading] = useState(false);
  const [txError, setTxError] = useState("");
  const [txOffset, setTxOffset] = useState(0);
  const [txLimit] = useState(25);
  const [transfers, setTransfers] = useState<any[]>([]);
  const [txHasMore, setTxHasMore] = useState(true);

  const nyxtBalance = useMemo(() => balances.find((b) => b.asset_id === "NYXT")?.balance ?? 0, [balances]);

  const loadBalances = async () => {
    if (!backendOnline || !session) return;
    setBalancesLoading(true);
    setBalancesError("");
    try {
      const payload = await fetchWalletBalancesV1(token, address);
      setAssets(payload.assets || []);
      setBalances(payload.balances || []);
      if ((payload.assets || []).length > 0) {
        setTransferAssetId((payload.assets?.[0]?.asset_id as string) || "NYXT");
      }
    } catch (err) {
      setBalancesError((err as Error).message);
    } finally {
      setBalancesLoading(false);
    }
  };

  const loadTransfers = async (opts?: { reset?: boolean }) => {
    if (!backendOnline || !session) return;
    setTxLoading(true);
    setTxError("");
    try {
      const nextOffset = opts?.reset ? 0 : txOffset;
      const payload = await fetchWalletTransfersV1(token, address, txLimit, nextOffset);
      const list = payload.transfers || [];
      if (opts?.reset) {
        setTransfers(list);
      } else {
        setTransfers((prev) => [...prev, ...list]);
      }
      setTxHasMore(list.length === txLimit);
      setTxOffset(nextOffset + list.length);
    } catch (err) {
      setTxError((err as Error).message);
    } finally {
      setTxLoading(false);
    }
  };

  useEffect(() => {
    loadBalances();
    loadTransfers({ reset: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [backendOnline, session?.access_token, session?.account_id]);

  const copyAddress = async () => {
    if (!address) return;
    try {
      await navigator.clipboard.writeText(address);
    } catch {
      // ignore
    }
  };

  const validateAddress = (value: string): boolean => /^[A-Za-z0-9_-]{1,64}$/.test(value);

  const handleSend = async () => {
    if (!backendOnline || !session) return;
    setTransferError("");

    const to = transferTo.trim();
    if (!validateAddress(to)) {
      setTransferError("Recipient address invalid.");
      return;
    }
    if (to === address) {
      setTransferError("Recipient must differ from sender.");
      return;
    }

    const amt = Number(transferAmount);
    if (!Number.isInteger(amt) || amt <= 0) {
      setTransferError("Amount must be a positive integer.");
      return;
    }

    let seedInt = 0;
    try {
      seedInt = parseSeed(seed);
    } catch (err) {
      setTransferError((err as Error).message);
      return;
    }

    const run_id = allocateRunId(runId, "wallet-transfer");
    setTransferLoading(true);
    try {
      await transferWallet(token, seedInt, run_id, address, to, amt, transferAssetId);
      setShowSend(false);
      setTransferTo("");
      setTransferAmount("1");
      await loadBalances();
      await loadTransfers({ reset: true });
    } catch (err) {
      setTransferError((err as Error).message);
    } finally {
      setTransferLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full text-text-main dark:text-white">
      {/* Account Header */}
      <div className="flex flex-col items-center py-8 bg-gradient-to-b from-primary/10 to-transparent rounded-b-3xl">
        <div className="size-16 rounded-full bg-gradient-to-tr from-primary to-primary-dark shadow-lg mb-4 flex items-center justify-center text-background-dark font-bold text-xl">
          {session?.handle?.[0]?.toUpperCase() ?? "N"}
        </div>
        <div className="text-lg font-bold mb-1">@{session?.handle ?? "user"}</div>
        <button
          onClick={copyAddress}
          className="flex items-center gap-2 px-3 py-1 rounded-full bg-surface-light dark:bg-surface-dark text-xs text-text-subtle hover:bg-opacity-80 transition-all"
        >
          {address ? `${address.slice(0, 6)}...${address.slice(-4)}` : "—"}
          <span className="material-symbols-outlined text-sm">content_copy</span>
        </button>
      </div>

      {/* Balance */}
      <div className="flex flex-col items-center py-6">
        <div className="text-4xl font-extrabold tracking-tight mb-2">
          {balancesLoading ? "…" : nyxtBalance.toLocaleString()}{" "}
          <span className="text-xl font-normal text-text-subtle">NYXT</span>
        </div>

        <div className="flex gap-4 mt-6">
          <ActionButton
            icon="add"
            label="Buy"
            disabled
            disabledReason="Fiat on-ramp is disabled in Testnet."
            onClick={() => {}}
          />
          <ActionButton icon="send" label="Send" onClick={() => setShowSend(true)} />
          <ActionButton icon="swap_horiz" label="Swap" onClick={() => onNavigate(Screen.EXCHANGE)} />
          <ActionButton icon="water_drop" label="Faucet" onClick={() => onNavigate(Screen.FAUCET as any)} />
        </div>

        {balancesError && (
          <div className="mt-4 text-xs text-binance-red bg-binance-red/10 border border-binance-red/20 px-3 py-2 rounded-xl">
            {balancesError}{" "}
            <button onClick={loadBalances} className="underline font-bold">
              Retry
            </button>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex-1 flex flex-col mt-4">
        <div className="flex border-b border-primary/10">
          <TabButton active={activeTab === "assets"} onClick={() => setActiveTab("assets")} label="Assets" />
          <TabButton active={activeTab === "activity"} onClick={() => setActiveTab("activity")} label="Activity" />
        </div>

        <div className="flex-1 overflow-y-auto p-4 no-scrollbar">
          {activeTab === "assets" ? (
            <div className="flex flex-col gap-4">
              {balancesLoading ? (
                <div className="p-4 rounded-2xl bg-surface-light dark:bg-surface-dark/40 border border-primary/5 text-sm text-text-subtle">
                  Loading balances…
                </div>
              ) : balances.length === 0 ? (
                <div className="p-4 rounded-2xl bg-surface-light dark:bg-surface-dark/40 border border-primary/5 text-sm text-text-subtle">
                  No assets found.
                </div>
              ) : (
                balances.map((b) => (
                  <AssetRow
                    key={b.asset_id}
                    symbol={b.asset_id}
                    name={assets.find((a) => a.asset_id === b.asset_id)?.name}
                    balance={b.balance}
                  />
                ))
              )}
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between px-1">
                <div className="text-xs font-bold text-text-subtle uppercase">Recent Transfers</div>
                <button
                  onClick={() => loadTransfers({ reset: true })}
                  className="text-[10px] font-bold text-primary uppercase tracking-widest"
                >
                  Refresh
                </button>
              </div>

              {txError && (
                <div className="p-4 rounded-2xl bg-binance-red/10 border border-binance-red/20 text-xs text-binance-red">
                  {txError}{" "}
                  <button onClick={() => loadTransfers({ reset: true })} className="underline font-bold">
                    Retry
                  </button>
                </div>
              )}

              {!txError && transfers.length === 0 && !txLoading && (
                <div className="flex flex-col items-center justify-center py-12 text-text-subtle">
                  <span className="material-symbols-outlined text-4xl mb-2 opacity-20">history</span>
                  <div className="text-sm">No transfers yet</div>
                  <button onClick={() => onNavigate(Screen.ACTIVITY)} className="mt-2 text-xs text-primary underline">
                    View Evidence Center
                  </button>
                </div>
              )}

              {transfers.map((t) => {
                const isIncoming = t.to_address === address;
                return (
                  <div
                    key={t.transfer_id}
                    className="p-4 rounded-2xl bg-surface-light dark:bg-surface-dark/40 border border-primary/5"
                  >
                    <div className="flex items-center justify-between">
                      <div className="text-xs font-bold">
                        {isIncoming ? "Receive" : "Send"} {t.amount} {t.asset_id}
                      </div>
                      <div
                        className={`text-[10px] font-bold ${t.replay_ok ? "text-binance-green" : "text-binance-red"}`}
                      >
                        {t.replay_ok ? "Verified" : "Unverified"}
                      </div>
                    </div>
                    <div className="mt-1 text-[10px] font-mono text-text-subtle break-all">run_id: {t.run_id}</div>
                    <div className="mt-2 flex gap-3 text-[10px] text-text-subtle">
                      <div>fee: {t.fee_total} NYXT</div>
                      <div>treasury: {t.treasury_address}</div>
                    </div>
                    <button
                      onClick={() => onNavigate(Screen.ACTIVITY)}
                      className="mt-2 text-[10px] font-bold text-primary underline"
                    >
                      Open Evidence
                    </button>
                  </div>
                );
              })}

              {txLoading && (
                <div className="p-4 rounded-2xl bg-surface-light dark:bg-surface-dark/40 border border-primary/5 text-xs text-text-subtle">
                  Loading…
                </div>
              )}

              {txHasMore && !txLoading && transfers.length > 0 && (
                <button
                  onClick={() => loadTransfers()}
                  className="w-full py-3 rounded-2xl bg-primary/10 text-primary text-xs font-bold border border-primary/20"
                >
                  Load more
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Send Modal */}
      {showSend && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60">
          <div className="w-full max-w-md rounded-t-3xl bg-background-light dark:bg-background-dark p-6 border-t border-primary/20">
            <div className="flex items-center justify-between">
              <div className="text-sm font-bold">Send</div>
              <button onClick={() => setShowSend(false)} className="text-text-subtle hover:text-primary">
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <div className="mt-4 flex flex-col gap-3">
              <label className="flex flex-col gap-1">
                <span className="text-[10px] font-bold text-text-subtle uppercase">To</span>
                <input
                  className="h-11 rounded-2xl bg-surface-light dark:bg-surface-dark/40 border border-primary/10 px-4 text-sm font-mono outline-none"
                  value={transferTo}
                  onChange={(e) => setTransferTo(e.target.value)}
                  placeholder="acct-…"
                />
              </label>

              <div className="grid grid-cols-2 gap-3">
                <label className="flex flex-col gap-1">
                  <span className="text-[10px] font-bold text-text-subtle uppercase">Amount</span>
                  <input
                    className="h-11 rounded-2xl bg-surface-light dark:bg-surface-dark/40 border border-primary/10 px-4 text-sm outline-none"
                    value={transferAmount}
                    onChange={(e) => setTransferAmount(e.target.value)}
                  />
                </label>

                <label className="flex flex-col gap-1">
                  <span className="text-[10px] font-bold text-text-subtle uppercase">Asset</span>
                  <select
                    className="h-11 rounded-2xl bg-surface-light dark:bg-surface-dark/40 border border-primary/10 px-4 text-sm outline-none"
                    value={transferAssetId}
                    onChange={(e) => setTransferAssetId(e.target.value)}
                  >
                    {(assets.length ? assets : [{ asset_id: "NYXT" }]).map((a) => (
                      <option key={a.asset_id} value={a.asset_id}>
                        {a.asset_id}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              {transferError && (
                <div className="text-xs text-binance-red bg-binance-red/10 border border-binance-red/20 px-3 py-2 rounded-xl">
                  {transferError}
                </div>
              )}

              <button
                onClick={handleSend}
                disabled={transferLoading}
                className={`h-12 rounded-2xl font-bold transition-all ${
                  transferLoading ? "bg-surface-light dark:bg-surface-dark text-text-subtle" : "bg-primary text-black"
                }`}
              >
                {transferLoading ? "Sending…" : "Send"}
              </button>

              <div className="text-[10px] text-text-subtle leading-relaxed">
                Every transfer produces an evidence bundle (receipt_hashes + state_hash) and routes fees to the testnet
                treasury.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const ActionButton: React.FC<{
  icon: string;
  label: string;
  onClick: () => void;
  disabled?: boolean;
  disabledReason?: string;
}> = ({ icon, label, onClick, disabled, disabledReason }) => (
  <button
    onClick={onClick}
    className="flex flex-col items-center gap-2 group"
    disabled={disabled}
    title={disabled ? disabledReason : ""}
  >
    <div
      className={`size-12 rounded-full flex items-center justify-center shadow-lg transition-transform ${
        disabled
          ? "bg-surface-light dark:bg-surface-dark text-text-subtle"
          : "bg-primary text-background-dark group-hover:scale-110"
      }`}
    >
      <span className="material-symbols-outlined">{icon}</span>
    </div>
    <span className={`text-xs font-bold ${disabled ? "text-text-subtle" : "text-primary"}`}>{label}</span>
  </button>
);

const TabButton: React.FC<{ active: boolean; onClick: () => void; label: string }> = ({ active, onClick, label }) => (
  <button
    onClick={onClick}
    className={`flex-1 py-4 text-sm font-bold transition-all border-b-2 ${
      active ? "text-primary border-primary" : "text-text-subtle border-transparent"
    }`}
  >
    {label}
  </button>
);

const AssetRow: React.FC<{ symbol: string; name?: string; balance: number }> = ({ symbol, name, balance }) => (
  <div className="flex items-center justify-between p-4 rounded-2xl bg-surface-light dark:bg-surface-dark/40 hover:bg-opacity-80 transition-all border border-primary/5">
    <div className="flex items-center gap-3">
      <div className="size-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold">
        {symbol[0]}
      </div>
      <div>
        <div className="font-bold text-sm">{symbol}</div>
        <div className="text-[10px] text-text-subtle uppercase">{name ?? "Asset"}</div>
      </div>
    </div>
    <div className="text-right">
      <div className="font-bold text-sm">{balance.toLocaleString()}</div>
      <div className="text-[10px] text-text-subtle">testnet</div>
    </div>
  </div>
);
