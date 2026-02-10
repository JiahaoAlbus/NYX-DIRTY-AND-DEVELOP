import React, { useEffect, useMemo, useState } from "react";
import { Droplets, Send, Info, ShieldCheck } from "lucide-react";
import { allocateRunId, faucetWallet, parseSeed, PortalSession } from "../api";
import { Screen } from "../types";
import { useI18n } from "../i18n";

type FaucetProps = {
  seed: string;
  runId: string;
  backendOnline: boolean;
  session: PortalSession | null;
  onNavigate?: (screen: Screen) => void;
};

export const Faucet: React.FC<FaucetProps> = ({ seed, runId, backendOnline, session, onNavigate }) => {
  const { t } = useI18n();
  const [address, setAddress] = useState(session?.wallet_address ?? "");
  const [assetId, setAssetId] = useState("NYXT");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [lastRunId, setLastRunId] = useState("");
  const [retryAfter, setRetryAfter] = useState<number | null>(null);

  const canSubmit = useMemo(
    () => backendOnline && !!session && !!address.trim() && !loading,
    [backendOnline, session, address, loading],
  );

  useEffect(() => {
    if (session?.wallet_address) {
      setAddress(session.wallet_address);
    }
  }, [session?.wallet_address]);

  const handleRequest = async () => {
    if (!canSubmit || !session) return;
    setLoading(true);
    setRetryAfter(null);
    setStatus(t("faucet.requesting"));

    let seedInt = 0;
    try {
      seedInt = parseSeed(seed);
    } catch (err) {
      setStatus((err as Error).message);
      setLoading(false);
      return;
    }

    const run_id = allocateRunId(runId, "wallet-faucet");
    setLastRunId(run_id);
    try {
      const res = await faucetWallet(session.access_token, seedInt, run_id, address.trim(), 1000, assetId);
      const feeTotal = (res as any).fee_total;
      const treasury = (res as any).treasury_address;
      const newBalance = (res as any).balance;
      setStatus(
        t("faucet.success", {
          amount: 1000,
          asset: assetId,
          balance: newBalance ?? "?",
          fee: feeTotal ?? "?",
          treasury: treasury ?? t("common.treasury"),
        }),
      );
    } catch (err) {
      const message = (err as Error).message;
      const details = (err as any)?.details;
      const ra = details?.retry_after_seconds;
      if (typeof ra === "number") setRetryAfter(ra);
      setStatus(t("faucet.error", { message }));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6 text-text-main dark:text-white pb-24">
      <div className="p-8 rounded-3xl glass-dark border border-white/10 flex flex-col items-center text-center">
        <div className="size-16 rounded-2xl bg-primary/20 flex items-center justify-center text-primary mb-4 shadow-inner">
          <Droplets size={32} />
        </div>
        <h2 className="text-xl font-bold">{t("faucet.title")}</h2>
        <p className="text-xs text-text-subtle mt-2">{t("faucet.subtitle")}</p>
      </div>

      <div className="p-6 rounded-3xl glass bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5 flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <label className="text-[10px] text-text-subtle uppercase px-1">{t("faucet.walletAddress")}</label>
          <div className="flex items-center gap-2 px-4 py-3 bg-background-light dark:bg-background-dark rounded-2xl border border-black/5 dark:border-white/5">
            <input
              className="bg-transparent flex-1 outline-none text-sm font-mono"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
            />
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-[10px] text-text-subtle uppercase px-1">{t("faucet.assetLabel")}</label>
          <select
            className="h-11 rounded-2xl bg-background-light dark:bg-background-dark border border-black/5 dark:border-white/5 px-4 text-sm outline-none"
            value={assetId}
            onChange={(e) => setAssetId(e.target.value)}
          >
            <option value="NYXT">NYXT</option>
            <option value="ECHO">ECHO</option>
            <option value="USDX">USDX</option>
          </select>
        </div>

        <div className="flex flex-col gap-4">
          <div className="p-4 rounded-2xl bg-primary/5 border border-primary/10 flex gap-3 items-start">
            <Info size={16} className="text-primary shrink-0 mt-0.5" />
            <div className="text-[10px] text-text-subtle leading-relaxed">{t("faucet.limitsNote")}</div>
          </div>

          <button
            onClick={handleRequest}
            disabled={!canSubmit}
            className={`w-full py-4 rounded-2xl font-bold flex items-center justify-center gap-2 transition-all ${
              !canSubmit
                ? "bg-surface-light dark:bg-surface-dark text-text-subtle"
                : "bg-primary text-black hover:scale-[1.02] active:scale-95"
            }`}
          >
            {loading ? (
              <div className="size-4 border-2 border-black/20 border-t-black rounded-full animate-spin" />
            ) : (
              <Send size={18} />
            )}
            {t("faucet.requestAmount", { amount: 1000, asset: assetId })}
          </button>

          {retryAfter !== null && (
            <div className="text-[10px] text-text-subtle">{t("faucet.retryAfter", { seconds: retryAfter })}</div>
          )}

          {lastRunId && (
            <div className="text-[10px] text-text-subtle">
              {t("common.runId")}: <span className="font-mono break-all">{lastRunId}</span>{" "}
              {onNavigate && (
                <button onClick={() => onNavigate(Screen.ACTIVITY)} className="underline text-primary font-bold ml-2">
                  {t("activity.openEvidence")}
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center justify-center gap-2 text-[10px] text-text-subtle">
        <ShieldCheck size={12} /> {t("faucet.deterministicNote")}
      </div>

      {status && (
        <div className="fixed bottom-24 left-1/2 -translate-x-1/2 px-6 py-3 rounded-2xl bg-primary text-black text-xs font-bold shadow-2xl animate-in fade-in slide-in-from-bottom-4">
          {status}
        </div>
      )}
    </div>
  );
};
