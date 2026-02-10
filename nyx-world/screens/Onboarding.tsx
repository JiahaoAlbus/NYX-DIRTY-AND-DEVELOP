import React, { useState } from "react";
import {
  createPortalAccount,
  derivePortalKey,
  fetchPortalChallenge,
  verifyPortalChallenge,
  PortalSession,
} from "../api";
import { useI18n } from "../i18n";

interface OnboardingProps {
  backendOnline: boolean;
  backendStatus: string;
  onRefresh: () => void;
  onComplete: (session: PortalSession) => void;
}

export const Onboarding: React.FC<OnboardingProps> = ({ backendOnline, backendStatus, onRefresh, onComplete }) => {
  const { t } = useI18n();
  const [handle, setHandle] = useState("");
  const [seed, setSeed] = useState("");
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);

  const createAccount = async () => {
    if (!backendOnline) {
      setStatus(t("onboarding.backendUnavailable"));
      return;
    }
    if (!handle.trim()) {
      setStatus(t("onboarding.handleRequired"));
      return;
    }
    if (!seed.trim()) {
      setStatus(t("onboarding.seedRequired"));
      return;
    }
    setBusy(true);
    setStatus(t("onboarding.createAccount"));
    try {
      const key = derivePortalKey(seed.trim());
      const account = await createPortalAccount(handle.trim(), key.pubkey);
      const challenge = await fetchPortalChallenge(account.account_id);
      const token = await verifyPortalChallenge(account.account_id, challenge.nonce, key.keyBytes);
      onComplete({
        account_id: account.account_id,
        handle: account.handle,
        pubkey: account.pubkey,
        access_token: token.access_token,
        wallet_address: account.wallet_address ?? token.wallet_address ?? "",
      });
    } catch (err) {
      setStatus(t("onboarding.error", { message: (err as Error).message }));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex flex-col gap-6 w-full p-6">
      <div className="text-lg font-semibold text-text-main">{t("onboarding.title")}</div>
      <div className="text-xs text-text-subtle">{t("onboarding.subtitle")}</div>
      <div className="rounded-lg border border-primary/20 bg-white/80 p-4">
        <div className="text-xs font-semibold text-text-subtle">{t("onboarding.backend")}</div>
        <div className="text-sm font-medium">{backendStatus}</div>
        <button onClick={onRefresh} className="mt-2 text-xs font-semibold text-primary underline">
          {t("common.refresh")}
        </button>
      </div>
      <div className="flex flex-col gap-3">
        <label className="flex flex-col gap-1">
          <span className="text-xs font-semibold">{t("onboarding.handle")}</span>
          <input
            className="h-10 rounded-lg border border-primary/20 px-3"
            value={handle}
            onChange={(e) => setHandle(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-xs font-semibold">{t("onboarding.seed")}</span>
          <input
            className="h-10 rounded-lg border border-primary/20 px-3"
            value={seed}
            onChange={(e) => setSeed(e.target.value)}
          />
        </label>
      </div>
      <button
        disabled={busy || !backendOnline}
        onClick={createAccount}
        className="h-11 rounded-xl bg-primary text-background-dark font-semibold"
      >
        {busy ? t("onboarding.working") : t("onboarding.create")}
      </button>
      {status && <div className="text-xs text-text-subtle">{status}</div>}
    </div>
  );
};
