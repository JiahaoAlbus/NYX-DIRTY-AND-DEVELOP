import React, { useEffect, useState } from "react";
import { Screen } from "../types";
import { fetchDiscoveryFeed } from "../api";
import type { Capabilities } from "../capabilities";
import { featureReasonText, featureStatus, isFeatureEnabled, isModuleUsable } from "../capabilities";
import {
  Zap,
  Droplets,
  ArrowLeftRight,
  ShoppingBag,
  MessageCircle,
  Wallet as WalletIcon,
  ShieldCheck,
  Globe,
} from "lucide-react";

interface HomeProps {
  backendOnline: boolean;
  backendStatus: string;
  capabilities: Capabilities | null;
  onRefresh: () => void;
  seed: string;
  runId: string;
  onNavigate: (screen: Screen) => void;
}

export const Home: React.FC<HomeProps> = ({ backendOnline, onRefresh, onNavigate, capabilities }) => {
  const [feed, setFeed] = useState<any[]>([]);
  const [feedError, setFeedError] = useState<string | null>(null);

  useEffect(() => {
    const loadFeed = async () => {
      if (!backendOnline) return;
      try {
        const data = await fetchDiscoveryFeed();
        const raw = Array.isArray(data.feed) ? data.feed : [];
        setFeed(raw.filter((item) => item?.type === "listing"));
        setFeedError(null);
      } catch (err) {
        setFeedError((err as Error).message);
      }
    };
    loadFeed();
  }, [backendOnline]);

  const canWallet = isModuleUsable(capabilities, "wallet");
  const canFaucet = isFeatureEnabled(capabilities, "wallet", "faucet");
  const canAirdrop = isFeatureEnabled(capabilities, "wallet", "airdrop");
  const canExchange = isFeatureEnabled(capabilities, "exchange", "trading");
  const canChat = isFeatureEnabled(capabilities, "chat", "dm");
  const canStore = isFeatureEnabled(capabilities, "marketplace", "purchase");
  const canDappBrowser = isFeatureEnabled(capabilities, "dapp", "browser");
  const canWeb2Guard = isFeatureEnabled(capabilities, "web2", "guard");

  return (
    <div className="flex flex-col gap-6 pb-24">
      {!capabilities && (
        <div className="rounded-3xl border border-primary/20 bg-surface-light dark:bg-surface-dark/40 p-5 text-xs text-text-subtle">
          Capabilities not loaded. Modules are gated by backend <code>/capabilities</code>.{" "}
          <button onClick={onRefresh} className="ml-2 font-bold text-primary underline">
            Refresh
          </button>
        </div>
      )}

      {/* Wallet Glance */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-primary to-primary-dark p-6 shadow-2xl glass">
        <div className="relative z-10 flex flex-col gap-2">
          <h2 className="text-2xl font-black text-black leading-tight">Secure Your Future with NYX</h2>
          <p className="text-xs font-bold text-black/60 uppercase tracking-widest">Deterministic Web3 Ecosystem</p>
          <button
            onClick={() => canAirdrop && onNavigate(Screen.AIRDROP)}
            disabled={!canAirdrop}
            title={canAirdrop ? undefined : featureReasonText(featureStatus(capabilities, "wallet", "airdrop"))}
            className={`mt-4 w-fit rounded-xl bg-black px-6 py-2.5 text-xs font-bold shadow-xl transition-all ${canAirdrop ? "text-primary hover:scale-105 active:scale-95" : "text-white/60 opacity-70 cursor-not-allowed"}`}
          >
            Claim Airdrop
          </button>
          {!canAirdrop && (
            <div className="text-[10px] font-bold text-black/50">
              Airdrop disabled: {featureReasonText(featureStatus(capabilities, "wallet", "airdrop"))}
            </div>
          )}
        </div>
        <div className="absolute -right-8 -top-8 size-48 rounded-full bg-black/5 blur-3xl" />
        <div className="absolute right-4 bottom-4 opacity-20 text-black">
          <Zap size={80} strokeWidth={3} />
        </div>
      </div>

      {/* Quick Actions Grid (Binance Style) */}
      <div className="grid grid-cols-4 gap-4">
        <Shortcut
          icon={<Droplets size={20} />}
          label="Faucet"
          disabled={!canFaucet}
          disabledReason={featureReasonText(featureStatus(capabilities, "wallet", "faucet"))}
          onClick={() => onNavigate(Screen.FAUCET)}
        />
        <Shortcut
          icon={<WalletIcon size={20} />}
          label="Wallet"
          disabled={!canWallet}
          disabledReason="Wallet disabled by backend capabilities."
          onClick={() => onNavigate(Screen.WALLET)}
        />
        <Shortcut
          icon={<ArrowLeftRight size={20} />}
          label="Trade"
          disabled={!canExchange}
          disabledReason={featureReasonText(featureStatus(capabilities, "exchange", "trading"))}
          onClick={() => onNavigate(Screen.EXCHANGE)}
        />
        <Shortcut
          icon={<ShoppingBag size={20} />}
          label="Store"
          disabled={!canStore}
          disabledReason={featureReasonText(featureStatus(capabilities, "marketplace", "purchase"))}
          onClick={() => onNavigate(Screen.STORE)}
        />
      </div>

      {/* Ecosystem Modules */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between px-2">
          <h3 className="text-sm font-bold uppercase tracking-widest text-text-subtle">Core Modules</h3>
          <button onClick={onRefresh} className="text-[10px] text-primary font-bold">
            Refresh Status
          </button>
        </div>

        <div className="grid grid-cols-1 gap-3">
          <ModuleCard
            icon={<WalletIcon className="text-primary" />}
            title="Web3 Wallet"
            desc="Secure MetaMask-style asset management"
            disabled={!canWallet}
            disabledReason="Disabled by backend capabilities."
            onClick={() => onNavigate(Screen.WALLET)}
          />
          <ModuleCard
            icon={<ArrowLeftRight className="text-binance-green" />}
            title="Exchange"
            desc="Pro-grade trading with deep liquidity"
            disabled={!canExchange}
            disabledReason={featureReasonText(featureStatus(capabilities, "exchange", "trading"))}
            onClick={() => onNavigate(Screen.EXCHANGE)}
          />
          <ModuleCard
            icon={<MessageCircle className="text-blue-400" />}
            title="Chat"
            desc="Instagram-style P2P encrypted social"
            disabled={!canChat}
            disabledReason={featureReasonText(featureStatus(capabilities, "chat", "dm"))}
            onClick={() => onNavigate(Screen.CHAT)}
          />
          <ModuleCard
            icon={<ShoppingBag className="text-orange-400" />}
            title="Store"
            desc="Deterministic marketplace for dApps"
            disabled={!canStore}
            disabledReason={featureReasonText(featureStatus(capabilities, "marketplace", "purchase"))}
            onClick={() => onNavigate(Screen.STORE)}
          />
          <ModuleCard
            icon={<Globe className="text-primary" />}
            title="dApp Browser"
            desc="Open dApps with your NYX wallet"
            disabled={!canDappBrowser}
            disabledReason={featureReasonText(featureStatus(capabilities, "dapp", "browser"))}
            onClick={() => onNavigate(Screen.DAPP_BROWSER)}
          />
          <ModuleCard
            icon={<ShieldCheck className="text-purple-400" />}
            title="Web2 Guard"
            desc="Encrypted access to external APIs"
            disabled={!canWeb2Guard}
            disabledReason={featureReasonText(featureStatus(capabilities, "web2", "guard"))}
            onClick={() => onNavigate(Screen.WEB2_ACCESS)}
          />
        </div>
      </div>

      {/* Discovery Feed: IG Style */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between px-2">
          <h3 className="font-black text-lg tracking-tight">Explore NYX</h3>
          <button onClick={onRefresh} className="text-xs font-bold text-primary">
            Refresh
          </button>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {feed.length === 0 ? (
            <div className="col-span-2 rounded-3xl border border-black/5 dark:border-white/5 bg-surface-light dark:bg-surface-dark/40 p-6 text-xs text-text-subtle">
              {feedError ? (
                <>Discovery feed unavailable: {feedError}</>
              ) : (
                <>
                  No live listings yet. Publish a listing in Store to populate the discovery feed.
                  <div className="mt-3 flex gap-2">
                    <button
                      onClick={() => onNavigate(Screen.STORE)}
                      className="rounded-xl bg-primary px-3 py-2 text-[10px] font-bold text-black"
                      disabled={!canStore}
                      title={
                        canStore ? undefined : featureReasonText(featureStatus(capabilities, "marketplace", "purchase"))
                      }
                    >
                      Open Store
                    </button>
                    <button
                      onClick={() => onNavigate(Screen.CHAT)}
                      className="rounded-xl border border-primary/20 px-3 py-2 text-[10px] font-bold text-primary"
                      disabled={!canChat}
                      title={canChat ? undefined : featureReasonText(featureStatus(capabilities, "chat", "dm"))}
                    >
                      Open Chat
                    </button>
                  </div>
                </>
              )}
            </div>
          ) : (
            feed.map((item, i) => (
              <button
                key={i}
                onClick={() => canStore && onNavigate(Screen.STORE)}
                disabled={!canStore}
                title={canStore ? undefined : featureReasonText(featureStatus(capabilities, "marketplace", "purchase"))}
                className={`aspect-square rounded-2xl bg-surface-light dark:bg-surface-dark overflow-hidden relative group text-left ${canStore ? "cursor-pointer" : "opacity-60 cursor-not-allowed"}`}
              >
                <img
                  src={`https://api.dicebear.com/7.x/initials/svg?seed=${item.data.name || item.data.title}`}
                  className="size-full object-cover group-hover:scale-110 transition-transform duration-500"
                  alt="feed-item"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex flex-col justify-end p-3">
                  <span className="text-[10px] font-bold text-primary">{item.type.toUpperCase()}</span>
                  <span className="text-xs font-bold text-white truncate">{item.data.name || item.data.title}</span>
                </div>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

const Shortcut: React.FC<{
  icon: React.ReactNode;
  label: string;
  disabled?: boolean;
  disabledReason?: string;
  onClick: () => void;
}> = ({ icon, label, disabled, disabledReason, onClick }) => (
  <button
    onClick={() => !disabled && onClick()}
    disabled={disabled}
    title={disabled ? disabledReason : undefined}
    className={`flex flex-col items-center gap-2 group ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
  >
    <div
      className={`size-12 rounded-2xl flex items-center justify-center border shadow-lg transition-all ${disabled ? "bg-surface-light/50 dark:bg-surface-dark/20 text-text-subtle border-black/5 dark:border-white/5" : "bg-surface-light dark:bg-surface-dark/40 text-primary border-black/5 dark:border-white/5 group-hover:bg-primary group-hover:text-black"}`}
    >
      {icon}
    </div>
    <span
      className={`text-[10px] font-bold ${disabled ? "text-text-subtle" : "text-text-subtle group-hover:text-text-main dark:text-white"}`}
    >
      {label}
    </span>
  </button>
);

const ModuleCard: React.FC<{
  icon: React.ReactNode;
  title: string;
  desc: string;
  disabled?: boolean;
  disabledReason?: string;
  onClick: () => void;
}> = ({ icon, title, desc, disabled, disabledReason, onClick }) => (
  <button
    onClick={() => !disabled && onClick()}
    disabled={disabled}
    title={disabled ? disabledReason : undefined}
    className={`flex items-center gap-4 p-4 rounded-3xl glass border border-black/5 dark:border-white/5 transition-all text-left group ${disabled ? "bg-surface-light/40 dark:bg-surface-dark/10 opacity-60 cursor-not-allowed" : "bg-surface-light dark:bg-surface-dark/20 hover:bg-surface-light/80 dark:hover:bg-surface-dark/40"}`}
  >
    <div className="size-12 rounded-2xl bg-surface-light dark:bg-surface-dark flex items-center justify-center shadow-inner group-hover:scale-110 transition-transform">
      {icon}
    </div>
    <div className="flex-1">
      <div className="text-sm font-bold">{title}</div>
      <div className="text-[10px] text-text-subtle line-clamp-1">{desc}</div>
      {disabled && disabledReason && (
        <div className="mt-1 text-[10px] font-bold text-binance-red">{disabledReason}</div>
      )}
    </div>
    <span className="material-symbols-outlined text-text-subtle opacity-0 group-hover:opacity-100 transition-all">
      chevron_right
    </span>
  </button>
);
