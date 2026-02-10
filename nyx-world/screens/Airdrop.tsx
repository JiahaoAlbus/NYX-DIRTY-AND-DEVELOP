import React, { useEffect, useMemo, useState } from "react";
import { Gift, CheckCircle2, Circle, Trophy, ShieldCheck } from "lucide-react";
import {
  allocateRunId,
  ApiError,
  AirdropTaskV1,
  claimAirdropV1,
  fetchAirdropTasksV1,
  parseSeed,
  PortalSession,
} from "../api";
import { useI18n } from "../i18n";

interface AirdropProps {
  seed: string;
  runId: string;
  backendOnline: boolean;
  session: PortalSession | null;
}

export const Airdrop: React.FC<AirdropProps> = ({ seed, runId, backendOnline, session }) => {
  const { t } = useI18n();
  const [tasks, setTasks] = useState<AirdropTaskV1[]>([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [lastClaim, setLastClaim] = useState<Record<string, unknown> | null>(null);

  const baseRunId = useMemo(() => (runId || "").trim() || "airdrop", [runId]);

  const loadTasks = async () => {
    if (!backendOnline) {
      setStatus(t("common.backendUnavailable"));
      return;
    }
    if (!session?.access_token) {
      setStatus(t("common.signInRequired"));
      return;
    }
    setLoading(true);
    setStatus(null);
    try {
      const payload = await fetchAirdropTasksV1(session.access_token);
      setTasks(payload.tasks || []);
    } catch (err) {
      const message = err instanceof ApiError ? `${err.code}: ${err.message}` : (err as Error).message;
      setStatus(t("airdrop.loadFailed", { message }));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [backendOnline, session?.access_token]);

  const handleClaim = async (taskId: string) => {
    if (!backendOnline || !session?.access_token) return;
    setLoading(true);
    setStatus(null);
    setLastClaim(null);
    try {
      const seedValue = parseSeed(seed.trim());
      const claimRunId = allocateRunId(baseRunId, `airdrop_${taskId}`);
      const result = await claimAirdropV1(session.access_token, seedValue, claimRunId, taskId);
      setLastClaim(result);
      await loadTasks();
    } catch (err) {
      const message = err instanceof ApiError ? `${err.code}: ${err.message}` : (err as Error).message;
      setStatus(t("airdrop.claimFailed", { message }));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6 text-text-main dark:text-white pb-24">
      <div className="p-8 rounded-3xl bg-gradient-to-br from-primary/20 to-purple-600/20 glass border border-white/10 flex flex-col items-center text-center">
        <div className="size-20 rounded-full bg-primary flex items-center justify-center text-black mb-4 shadow-2xl">
          <Trophy size={40} />
        </div>
        <h2 className="text-2xl font-bold">{t("airdrop.title")}</h2>
        <p className="text-sm text-text-subtle mt-2">{t("airdrop.subtitle")}</p>
      </div>

      <div className="flex flex-col gap-4">
        <h3 className="font-bold px-2 flex items-center gap-2">
          <Gift size={18} className="text-primary" /> {t("airdrop.availableTasks")}
        </h3>
        {tasks.length === 0 ? (
          <div className="p-6 rounded-3xl glass bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5 text-xs text-text-subtle">
            {loading
              ? t("airdrop.loadingTasks")
              : backendOnline
                ? t("airdrop.noTasks")
                : t("common.backendUnavailable")}
          </div>
        ) : (
          tasks.map((task) => (
            <div
              key={task.task_id}
              className="p-5 rounded-3xl glass bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5 flex items-center justify-between group"
            >
              <div className="flex items-center gap-4">
                <div
                  className={`size-10 rounded-xl flex items-center justify-center ${task.claimed ? "bg-binance-green/20 text-binance-green" : task.completed ? "bg-primary/20 text-primary" : "bg-black/5 dark:bg-white/5 text-text-subtle"}`}
                >
                  {task.claimed ? (
                    <CheckCircle2 size={24} />
                  ) : task.completed ? (
                    <Circle size={24} />
                  ) : (
                    <Circle size={24} />
                  )}
                </div>
                <div>
                  <div className="font-bold text-sm">{task.title}</div>
                  <div className="text-[10px] text-text-subtle">{task.description}</div>
                  <div className="text-xs text-primary">+{task.reward} NYXT</div>
                  {task.completion_run_id && (
                    <div className="mt-1 flex items-center gap-1 text-[10px] font-mono text-text-subtle">
                      <ShieldCheck size={12} className="text-binance-green" />
                      {t("common.completionRunId")}: {task.completion_run_id}
                    </div>
                  )}
                </div>
              </div>
              <button
                onClick={() => handleClaim(task.task_id)}
                disabled={!task.claimable || loading}
                title={
                  task.claimed
                    ? t("airdrop.claimedTitle", { runId: task.claim_run_id ?? "" })
                    : task.completed
                      ? undefined
                      : t("airdrop.completeTaskFirst")
                }
                className={`px-6 py-2 rounded-xl text-xs font-bold transition-all ${
                  task.claimable
                    ? "bg-primary text-black hover:scale-105 active:scale-95"
                    : "bg-surface-light dark:bg-surface-dark text-text-subtle opacity-70 cursor-not-allowed"
                }`}
              >
                {task.claimed
                  ? t("airdrop.claimed")
                  : task.claimable
                    ? t("airdrop.claim")
                    : task.completed
                      ? t("airdrop.ready")
                      : t("airdrop.incomplete")}
              </button>
            </div>
          ))
        )}
      </div>

      {lastClaim && (
        <div className="p-5 rounded-3xl bg-black/5 dark:bg-white/5 border border-white/10 text-xs">
          <div className="font-bold">{t("airdrop.lastClaimReceipt")}</div>
          <div className="mt-2 grid grid-cols-1 gap-1 font-mono text-[10px] text-text-subtle break-all">
            {"run_id" in lastClaim && (
              <div>
                {t("common.runId")}: {String((lastClaim as any).run_id)}
              </div>
            )}
            {"state_hash" in lastClaim && (
              <div>
                {t("common.stateHash")}: {String((lastClaim as any).state_hash)}
              </div>
            )}
            {"receipt_hashes" in lastClaim && (
              <div>
                {t("common.receiptHashes")}: {JSON.stringify((lastClaim as any).receipt_hashes)}
              </div>
            )}
            {"fee_total" in lastClaim && (
              <div>
                {t("activity.feeTotal")} {String((lastClaim as any).fee_total)}
              </div>
            )}
            {"treasury_address" in lastClaim && (
              <div>
                {t("activity.treasury")} {String((lastClaim as any).treasury_address)}
              </div>
            )}
            {"balance" in lastClaim && (
              <div>
                {t("airdrop.balanceLabel", { asset: "NYXT" })}: {String((lastClaim as any).balance)}
              </div>
            )}
          </div>
        </div>
      )}

      {status && (
        <div className="fixed bottom-24 left-1/2 -translate-x-1/2 px-6 py-3 rounded-2xl bg-binance-red text-white text-sm font-bold shadow-2xl">
          {status}
        </div>
      )}
    </div>
  );
};
