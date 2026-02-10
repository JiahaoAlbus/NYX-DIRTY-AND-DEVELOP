import React from "react";
import { Screen } from "../types";
import type { Capabilities } from "../capabilities";
import { featureReasonText, featureStatus, isFeatureEnabled, isModuleUsable } from "../capabilities";
import { useI18n } from "../i18n";

interface BottomNavProps {
  activeTab: Screen;
  onTabChange: (tab: Screen) => void;
  capabilities: Capabilities | null;
}

export const BottomNav: React.FC<BottomNavProps> = ({ activeTab, onTabChange, capabilities }) => {
  const { t } = useI18n();
  const getButtonClass = (isActive: boolean) =>
    `flex flex-1 flex-col items-center gap-1 p-2 group transition-colors duration-300 ${isActive ? "text-text-main dark:text-white" : "text-text-subtle dark:text-gray-400 hover:text-text-main dark:hover:text-primary"}`;

  const tabEnabled = (screen: Screen): { enabled: boolean; reason?: string } => {
    if (screen === Screen.HOME) return { enabled: true };
    if (screen === Screen.SETTINGS) return { enabled: true };
    if (screen === Screen.ACTIVITY) return { enabled: true };
    if (screen === Screen.EVIDENCE) return { enabled: true };
    if (!capabilities) return { enabled: false, reason: t("capabilities.notLoaded") };

    if (screen === Screen.WALLET) {
      const ok = isModuleUsable(capabilities, "wallet");
      return ok ? { enabled: true } : { enabled: false, reason: t("capabilities.disabled") };
    }
    if (screen === Screen.EXCHANGE) {
      const ok = isFeatureEnabled(capabilities, "exchange", "trading");
      return ok
        ? { enabled: true }
        : { enabled: false, reason: featureReasonText(featureStatus(capabilities, "exchange", "trading")) };
    }
    if (screen === Screen.CHAT) {
      const ok = isFeatureEnabled(capabilities, "chat", "dm");
      return ok
        ? { enabled: true }
        : { enabled: false, reason: featureReasonText(featureStatus(capabilities, "chat", "dm")) };
    }
    if (screen === Screen.STORE) {
      const ok = isFeatureEnabled(capabilities, "marketplace", "purchase");
      return ok
        ? { enabled: true }
        : { enabled: false, reason: featureReasonText(featureStatus(capabilities, "marketplace", "purchase")) };
    }
    return { enabled: true };
  };

  return (
    <nav className="fixed bottom-0 z-40 w-full max-w-md mx-auto bg-white/90 dark:bg-[#1f1c13]/90 backdrop-blur-xl border-t border-primary/10 pb-safe">
      <div className="flex items-center justify-between px-1 pt-2 pb-2">
        {/* World (Home) */}
        <button className={getButtonClass(activeTab === Screen.HOME)} onClick={() => onTabChange(Screen.HOME)}>
          <span
            className={`material-symbols-outlined text-[22px] ${activeTab === Screen.HOME ? "filled text-primary" : ""}`}
          >
            public
          </span>
          <span className="text-[9px] font-medium">{t("nav.home")}</span>
        </button>

        {/* Wallet */}
        {(() => {
          const guard = tabEnabled(Screen.WALLET);
          return (
            <button
              className={`${getButtonClass(activeTab === Screen.WALLET)} ${guard.enabled ? "" : "opacity-40 cursor-not-allowed"}`}
              onClick={() => guard.enabled && onTabChange(Screen.WALLET)}
              title={guard.enabled ? undefined : guard.reason}
              disabled={!guard.enabled}
            >
              <span
                className={`material-symbols-outlined text-[22px] ${activeTab === Screen.WALLET ? "filled text-primary" : ""}`}
              >
                account_balance_wallet
              </span>
              <span className="text-[9px] font-medium">{t("nav.wallet")}</span>
            </button>
          );
        })()}

        {/* Exchange */}
        {(() => {
          const guard = tabEnabled(Screen.EXCHANGE);
          return (
            <button
              className={`${getButtonClass(activeTab === Screen.EXCHANGE)} ${guard.enabled ? "" : "opacity-40 cursor-not-allowed"}`}
              onClick={() => guard.enabled && onTabChange(Screen.EXCHANGE)}
              title={guard.enabled ? undefined : guard.reason}
              disabled={!guard.enabled}
            >
              <span
                className={`material-symbols-outlined text-[22px] ${activeTab === Screen.EXCHANGE ? "filled text-primary" : ""}`}
              >
                currency_exchange
              </span>
              <span className="text-[9px] font-medium">{t("nav.trade")}</span>
            </button>
          );
        })()}

        {/* Chat */}
        {(() => {
          const guard = tabEnabled(Screen.CHAT);
          return (
            <button
              className={`${getButtonClass(activeTab === Screen.CHAT)} ${guard.enabled ? "" : "opacity-40 cursor-not-allowed"}`}
              onClick={() => guard.enabled && onTabChange(Screen.CHAT)}
              title={guard.enabled ? undefined : guard.reason}
              disabled={!guard.enabled}
            >
              <span
                className={`material-symbols-outlined text-[22px] ${activeTab === Screen.CHAT ? "filled text-primary" : ""}`}
              >
                chat_bubble
              </span>
              <span className="text-[9px] font-medium">{t("nav.chat")}</span>
            </button>
          );
        })()}

        {/* Store */}
        {(() => {
          const guard = tabEnabled(Screen.STORE);
          return (
            <button
              className={`${getButtonClass(activeTab === Screen.STORE)} ${guard.enabled ? "" : "opacity-40 cursor-not-allowed"}`}
              onClick={() => guard.enabled && onTabChange(Screen.STORE)}
              title={guard.enabled ? undefined : guard.reason}
              disabled={!guard.enabled}
            >
              <span
                className={`material-symbols-outlined text-[22px] ${activeTab === Screen.STORE ? "filled text-primary" : ""}`}
              >
                storefront
              </span>
              <span className="text-[9px] font-medium">{t("nav.store")}</span>
            </button>
          );
        })()}

        {/* Activity */}
        <button className={getButtonClass(activeTab === Screen.ACTIVITY)} onClick={() => onTabChange(Screen.ACTIVITY)}>
          <span
            className={`material-symbols-outlined text-[22px] ${activeTab === Screen.ACTIVITY ? "filled text-primary" : ""}`}
          >
            history
          </span>
          <span className="text-[9px] font-medium">{t("nav.activity")}</span>
        </button>

        {/* Evidence */}
        <button className={getButtonClass(activeTab === Screen.EVIDENCE)} onClick={() => onTabChange(Screen.EVIDENCE)}>
          <span
            className={`material-symbols-outlined text-[22px] ${activeTab === Screen.EVIDENCE ? "filled text-primary" : ""}`}
          >
            verified
          </span>
          <span className="text-[9px] font-medium">{t("nav.proof")}</span>
        </button>

        {/* Settings */}
        <button className={getButtonClass(activeTab === Screen.SETTINGS)} onClick={() => onTabChange(Screen.SETTINGS)}>
          <span
            className={`material-symbols-outlined text-[22px] ${activeTab === Screen.SETTINGS ? "filled text-primary" : ""}`}
          >
            settings
          </span>
          <span className="text-[9px] font-medium">{t("nav.settings")}</span>
        </button>
      </div>
    </nav>
  );
};
