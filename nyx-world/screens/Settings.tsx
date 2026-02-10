import React from "react";
import { PortalSession } from "../api";
import { useI18n } from "../i18n";

interface SettingsProps {
  session: PortalSession | null;
  seed: string;
  runId: string;
  onSeedChange: (v: string) => void;
  onRunIdChange: (v: string) => void;
  onLogout: () => void;
}

export const Settings: React.FC<SettingsProps> = ({ session, seed, runId, onSeedChange, onRunIdChange, onLogout }) => {
  const { t, locale, setLocale } = useI18n();
  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-xl font-bold">{t("settings.title")}</h2>

      <div className="flex flex-col gap-4">
        <section className="p-4 rounded-xl bg-white border border-primary/20 shadow-sm">
          <h3 className="text-sm font-bold uppercase text-text-subtle mb-3">{t("settings.account")}</h3>
          <div className="flex flex-col gap-2">
            <div className="text-sm font-medium">
              {t("settings.handle")}: @{session?.handle}
            </div>
            <div className="text-[10px] font-mono break-all text-text-subtle">
              {t("settings.accountId")}: {session?.account_id}
            </div>
            <div className="text-[10px] font-mono break-all text-text-subtle">
              {t("settings.walletAddress")}: {session?.wallet_address ?? t("common.notAvailable")}
            </div>
            <button onClick={onLogout} className="mt-2 text-sm font-bold text-red-600 underline text-left">
              {t("settings.logout")}
            </button>
          </div>
        </section>

        <section className="p-4 rounded-xl bg-white border border-primary/20 shadow-sm glass">
          <h3 className="text-sm font-bold uppercase text-text-subtle mb-3">{t("settings.language")}</h3>
          <div className="flex flex-col gap-2">
            <label className="text-xs font-medium">{t("settings.languageLabel")}</label>
            <select
              className="h-9 rounded-lg border border-primary/20 bg-white/50 px-3 text-sm outline-none focus:border-primary transition-all"
              value={locale}
              onChange={(e) => setLocale(e.target.value as "en" | "zh")}
            >
              <option value="en">{t("settings.languageEnglish")}</option>
              <option value="zh">{t("settings.languageChinese")}</option>
            </select>
          </div>
        </section>

        <section className="p-4 rounded-xl bg-white border border-primary/20 shadow-sm glass">
          <h3 className="text-sm font-bold uppercase text-text-subtle mb-3">{t("settings.deterministicRun")}</h3>
          <div className="flex flex-col gap-3">
            <label className="flex flex-col gap-1">
              <span className="text-xs font-medium">{t("settings.globalSeed")}</span>
              <input
                className="h-9 rounded-lg border border-primary/20 bg-white/50 px-3 text-sm outline-none focus:border-primary transition-all"
                value={seed}
                onChange={(e) => onSeedChange(e.target.value)}
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs font-medium">{t("settings.runId")}</span>
              <input
                className="h-9 rounded-lg border border-primary/20 bg-white/50 px-3 text-sm outline-none focus:border-primary transition-all"
                value={runId}
                onChange={(e) => onRunIdChange(e.target.value)}
              />
            </label>
          </div>
          <div className="mt-4 p-3 rounded-xl bg-primary/5 border border-primary/10 text-[10px] text-text-subtle leading-relaxed italic">
            {t("settings.runNote")}
          </div>
        </section>

        <section className="p-4 rounded-xl bg-white border border-primary/20 shadow-sm glass">
          <h3 className="text-sm font-bold uppercase text-text-subtle mb-3">{t("settings.treasuryFees")}</h3>
          <div className="text-xs text-text-subtle leading-relaxed">{t("settings.treasuryFeesNote")}</div>
        </section>

        <section className="p-4 rounded-xl bg-white border border-primary/20 shadow-sm">
          <h3 className="text-sm font-bold uppercase text-text-subtle mb-3">{t("settings.about")}</h3>
          <div className="text-xs text-text-subtle leading-relaxed">{t("settings.aboutNote")}</div>
        </section>
      </div>
    </div>
  );
};
