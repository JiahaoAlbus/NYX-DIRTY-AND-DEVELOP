import React, { useEffect, useMemo, useState } from "react";
import { ExternalLink, Globe, RefreshCw } from "lucide-react";
import { useI18n } from "../i18n";

type NormalizedUrl = { ok: true; url: string } | { ok: false; reason: string };

export const DappBrowser: React.FC = () => {
  const { t } = useI18n();
  const [url, setUrl] = useState("");
  const [activeUrl, setActiveUrl] = useState<string | null>(null);
  const [mode, setMode] = useState<"tab" | "embed">("tab");
  const [iframeKey, setIframeKey] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recents, setRecents] = useState<string[]>([]);

  const recentsKey = "nyx:dapp_recents:v1";

  useEffect(() => {
    try {
      const raw = localStorage.getItem(recentsKey);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        const cleaned = parsed.filter((v) => typeof v === "string" && v.length > 0).slice(0, 8);
        setRecents(cleaned);
      }
    } catch {
      // ignore
    }
  }, []);

  const normalize = (raw: string): NormalizedUrl => {
    const trimmed = (raw || "").trim();
    if (!trimmed) return { ok: false, reason: t("dapp.urlRequired") };
    const withScheme = /^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//.test(trimmed) ? trimmed : `https://${trimmed}`;
    let parsed: URL;
    try {
      parsed = new URL(withScheme);
    } catch {
      return { ok: false, reason: t("dapp.invalidUrl") };
    }
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
      return { ok: false, reason: t("dapp.protocolOnly") };
    }
    return { ok: true, url: parsed.toString() };
  };

  const persistRecent = (target: string) => {
    try {
      const next = [target, ...recents.filter((v) => v !== target)].slice(0, 8);
      setRecents(next);
      localStorage.setItem(recentsKey, JSON.stringify(next));
    } catch {
      // ignore
    }
  };

  const openNewTab = (target: string) => {
    window.open(target, "_blank", "noopener,noreferrer");
  };

  const go = (nextMode: "tab" | "embed") => {
    const normalized = normalize(url);
    if (normalized.ok === false) {
      setError(normalized.reason);
      return;
    }
    setError(null);
    setActiveUrl(normalized.url);
    setMode(nextMode);
    persistRecent(normalized.url);
    if (nextMode === "tab") {
      openNewTab(normalized.url);
    } else {
      setIsLoading(true);
      setIframeKey((k) => k + 1);
    }
  };

  const quickLinks = useMemo(
    () => [
      { label: "Jupiter", url: "https://jup.ag" },
      { label: "Uniswap", url: "https://app.uniswap.org" },
      { label: "Magic Eden", url: "https://magiceden.io" },
    ],
    [],
  );

  return (
    <div className="flex flex-col gap-6 text-text-main dark:text-white pb-24">
      <div className="p-8 rounded-3xl bg-gradient-to-br from-primary/20 to-purple-600/20 glass border border-white/10 flex flex-col items-center text-center">
        <div className="size-20 rounded-full bg-primary/20 flex items-center justify-center text-primary mb-4 shadow-2xl border border-primary/30">
          <Globe size={40} />
        </div>
        <h2 className="text-2xl font-bold">{t("dapp.title")}</h2>
        <p className="text-sm text-text-subtle mt-2">{t("dapp.subtitle")}</p>
      </div>

      <div className="p-6 rounded-3xl glass bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5 flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <label className="text-[10px] text-text-subtle uppercase px-1">{t("common.url")}</label>
          <div className="flex items-center gap-3 px-4 py-3 bg-background-light dark:bg-background-dark rounded-2xl border border-black/5 dark:border-white/5">
            <Globe size={18} className="text-text-subtle" />
            <input
              className="bg-transparent flex-1 outline-none text-sm font-mono"
              placeholder={t("dapp.placeholder")}
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") go("tab");
              }}
            />
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => go("tab")}
            className="flex-1 py-3 rounded-2xl bg-primary text-black font-bold flex items-center justify-center gap-2 hover:scale-[1.01] active:scale-[0.99] transition-all shadow-xl"
          >
            <ExternalLink size={16} />
            {t("dapp.openTab")}
          </button>
          <button
            onClick={() => go("embed")}
            className="flex-1 py-3 rounded-2xl border border-primary/20 text-primary font-bold flex items-center justify-center gap-2 hover:bg-primary/10 transition-all"
          >
            {t("dapp.embed")}
          </button>
        </div>

        {error && (
          <div className="rounded-2xl border border-binance-red/30 bg-binance-red/10 px-4 py-3 text-[11px] font-bold text-binance-red">
            {error}
          </div>
        )}

        <div className="flex flex-col gap-2">
          <div className="text-[10px] text-text-subtle uppercase px-1">{t("dapp.quickLinks")}</div>
          <div className="grid grid-cols-3 gap-2">
            {quickLinks.map((link) => (
              <button
                key={link.url}
                onClick={() => {
                  setUrl(link.url);
                  setError(null);
                  setActiveUrl(link.url);
                  setMode("tab");
                  persistRecent(link.url);
                  openNewTab(link.url);
                }}
                className="rounded-2xl border border-black/5 dark:border-white/10 bg-background-light dark:bg-background-dark px-3 py-2 text-[11px] font-bold hover:border-primary/30 hover:text-primary transition-colors"
                title={link.url}
              >
                {link.label}
              </button>
            ))}
          </div>
        </div>

        {recents.length > 0 && (
          <div className="flex flex-col gap-2">
            <div className="text-[10px] text-text-subtle uppercase px-1">{t("dapp.recent")}</div>
            <div className="flex flex-col gap-2">
              {recents.map((r) => (
                <button
                  key={r}
                  onClick={() => {
                    setUrl(r);
                    setError(null);
                    setActiveUrl(r);
                    setMode("tab");
                    openNewTab(r);
                  }}
                  className="rounded-2xl border border-black/5 dark:border-white/10 bg-background-light dark:bg-background-dark px-4 py-3 text-left text-[10px] font-mono text-text-subtle hover:border-primary/30 transition-colors break-all"
                  title={t("dapp.openTab")}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="rounded-3xl glass bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5 overflow-hidden min-h-[420px]">
        {!activeUrl ? (
          <div className="flex items-center justify-center h-[420px] text-text-subtle text-sm">{t("dapp.empty")}</div>
        ) : mode === "tab" ? (
          <div className="p-6 flex flex-col gap-4">
            <div className="text-sm font-bold">{t("dapp.opened")}</div>
            <div className="text-[11px] text-text-subtle">{t("dapp.openedHint")}</div>
            <div className="rounded-2xl border border-black/5 dark:border-white/10 bg-background-light dark:bg-background-dark px-4 py-3 text-[10px] font-mono text-text-subtle break-all">
              {activeUrl}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => openNewTab(activeUrl)}
                className="flex-1 py-3 rounded-2xl bg-primary text-black font-bold flex items-center justify-center gap-2 hover:scale-[1.01] active:scale-[0.99] transition-all"
              >
                <ExternalLink size={16} />
                {t("dapp.openAgain")}
              </button>
              <button
                onClick={() => {
                  setMode("embed");
                  setIsLoading(true);
                  setIframeKey((k) => k + 1);
                }}
                className="flex-1 py-3 rounded-2xl border border-primary/20 text-primary font-bold flex items-center justify-center gap-2 hover:bg-primary/10 transition-all"
              >
                {t("dapp.embedHere")}
              </button>
            </div>
          </div>
        ) : (
          <div className="relative h-[420px]">
            {isLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-background-light/70 dark:bg-background-dark/70 backdrop-blur-sm z-10">
                <div className="text-xs font-bold text-text-subtle">{t("dapp.loading")}</div>
              </div>
            )}
            <div className="absolute right-3 top-3 z-20">
              <button
                onClick={() => {
                  setIsLoading(true);
                  setIframeKey((k) => k + 1);
                }}
                className="size-9 rounded-2xl bg-background-light dark:bg-background-dark border border-black/5 dark:border-white/10 flex items-center justify-center text-text-subtle hover:text-primary transition-colors"
                title={t("dapp.reloadEmbed")}
              >
                <RefreshCw size={16} />
              </button>
            </div>
            <iframe
              key={iframeKey}
              src={activeUrl}
              className="w-full h-[420px] border-none"
              title={t("dapp.viewTitle")}
              onLoad={() => setIsLoading(false)}
            />
            <div className="px-4 py-3 text-[10px] text-text-subtle border-t border-black/5 dark:border-white/10">
              {t("dapp.embedBlocked")}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
