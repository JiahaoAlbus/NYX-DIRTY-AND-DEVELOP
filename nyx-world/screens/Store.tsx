import React, { useEffect, useMemo, useState } from "react";
import {
  allocateRunId,
  ApiError,
  fetchMyPurchasesV1,
  fetchWalletBalancesV1,
  listMarketplaceListings,
  parseSeed,
  PortalSession,
  publishListing,
  purchaseMarketplace,
  searchMarketplaceListings,
} from "../api";
import { Screen } from "../types";
import { useI18n } from "../i18n";
import { getStoredLocale, translate } from "../i18nCore";

type ListingRow = {
  listing_id: string;
  publisher_id: string;
  sku: string;
  title: string;
  price: number;
  status: "active" | "sold";
  run_id: string;
};

type PurchaseRow = {
  purchase_id: string;
  listing_id: string;
  buyer_id: string;
  qty: number;
  run_id: string;
  publisher_id?: string;
  sku?: string;
  title?: string;
  price?: number;
  status?: string;
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

interface StoreProps {
  seed: string;
  runId: string;
  backendOnline: boolean;
  session: PortalSession | null;
  onNavigate: (screen: Screen) => void;
}

const PAGE_LIMIT = 20;

function renderApiError(err: unknown): string {
  const locale = getStoredLocale();
    if (err instanceof ApiError) {
      const bits = [err.message];
      if (err.code && !err.message.includes(err.code)) bits.push(`(${err.code})`);
      const retryAfter = err.details?.retry_after_seconds;
      if (typeof retryAfter === "number" && Number.isFinite(retryAfter)) {
      bits.push(translate("common.retryAfter", { seconds: retryAfter }, locale));
      }
      return bits.join(" ");
    }
  return (err as Error)?.message ?? translate("common.unknownError", undefined, locale);
}

function formatCompactId(value: string): string {
  const v = (value || "").trim();
  if (v.length <= 18) return v;
  return `${v.slice(0, 10)}…${v.slice(-6)}`;
}

export const Store: React.FC<StoreProps> = ({ seed, runId, backendOnline, session, onNavigate }) => {
  const { t } = useI18n();
  const token = session?.access_token ?? "";
  const walletAddress = session?.wallet_address ?? "";

  const [tab, setTab] = useState<"shop" | "orders">("shop");

  const [query, setQuery] = useState("");
  const searchActive = useMemo(() => query.trim().length > 0, [query]);

  const [nyxtBalance, setNyxtBalance] = useState<number | null>(null);
  const [balanceError, setBalanceError] = useState("");

  const [listings, setListings] = useState<ListingRow[]>([]);
  const [listingsLoading, setListingsLoading] = useState(false);
  const [listingsError, setListingsError] = useState("");
  const [listingsOffset, setListingsOffset] = useState(0);
  const [listingsHasMore, setListingsHasMore] = useState(true);

  const [purchases, setPurchases] = useState<PurchaseRow[]>([]);
  const [purchasesLoading, setPurchasesLoading] = useState(false);
  const [purchasesError, setPurchasesError] = useState("");
  const [purchasesOffset, setPurchasesOffset] = useState(0);
  const [purchasesHasMore, setPurchasesHasMore] = useState(true);

  const [showPublish, setShowPublish] = useState(false);
  const [publishSku, setPublishSku] = useState("");
  const [publishTitle, setPublishTitle] = useState("");
  const [publishPrice, setPublishPrice] = useState("10");
  const [publishError, setPublishError] = useState("");

  const [buyListing, setBuyListing] = useState<ListingRow | null>(null);
  const [buyQty, setBuyQty] = useState("1");
  const [buyError, setBuyError] = useState("");

  const [mutating, setMutating] = useState(false);
  const [toast, setToast] = useState("");
  const [lastAction, setLastAction] = useState<RunResult | null>(null);

  const loadBalance = async () => {
    if (!backendOnline || !session) return;
    setBalanceError("");
    try {
      const payload = await fetchWalletBalancesV1(token, walletAddress);
      const nyxt = payload.balances?.find((b: any) => b.asset_id === "NYXT")?.balance ?? 0;
      setNyxtBalance(Number(nyxt));
    } catch (err) {
      setBalanceError(renderApiError(err));
      setNyxtBalance(null);
    }
  };

  const loadListings = async (opts?: { reset?: boolean }) => {
    if (!backendOnline) return;
    setListingsLoading(true);
    setListingsError("");
    try {
      const nextOffset = opts?.reset ? 0 : listingsOffset;
      const payload = searchActive
        ? await searchMarketplaceListings(query.trim(), PAGE_LIMIT, nextOffset)
        : await listMarketplaceListings(PAGE_LIMIT, nextOffset);
      const list = (payload.listings as ListingRow[]) || [];
      if (opts?.reset) setListings(list);
      else setListings((prev) => [...prev, ...list]);
      setListingsHasMore(list.length === PAGE_LIMIT);
      setListingsOffset(nextOffset + list.length);
    } catch (err) {
      setListingsError(renderApiError(err));
    } finally {
      setListingsLoading(false);
    }
  };

  const loadPurchases = async (opts?: { reset?: boolean }) => {
    if (!backendOnline || !session) return;
    setPurchasesLoading(true);
    setPurchasesError("");
    try {
      const nextOffset = opts?.reset ? 0 : purchasesOffset;
      const payload = await fetchMyPurchasesV1(token, PAGE_LIMIT, nextOffset);
      const list = (payload.purchases as PurchaseRow[]) || [];
      if (opts?.reset) setPurchases(list);
      else setPurchases((prev) => [...prev, ...list]);
      setPurchasesHasMore(list.length === PAGE_LIMIT);
      setPurchasesOffset(nextOffset + list.length);
    } catch (err) {
      setPurchasesError(renderApiError(err));
    } finally {
      setPurchasesLoading(false);
    }
  };

  const refreshAll = async () => {
    await loadBalance();
    await loadListings({ reset: true });
    await loadPurchases({ reset: true });
  };

  useEffect(() => {
    refreshAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [backendOnline, session?.access_token, session?.wallet_address]);

  useEffect(() => {
    loadListings({ reset: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchActive, query]);

  const handlePublish = async () => {
    if (!backendOnline || !session) return;
    setPublishError("");
    setToast("");
    setLastAction(null);

    const sku = publishSku.trim();
    const title = publishTitle.trim();
    if (!sku) {
      setPublishError(t("store.skuRequired"));
      return;
    }
    if (!title) {
      setPublishError(t("store.titleRequired"));
      return;
    }
    const px = Number(publishPrice);
    if (!Number.isInteger(px) || px <= 0) {
      setPublishError(t("store.pricePositive"));
      return;
    }

    let seedInt = 0;
    try {
      seedInt = parseSeed(seed);
    } catch (err) {
      setPublishError(renderApiError(err));
      return;
    }

    const deterministicRunId = allocateRunId(runId, "marketplace-listing-publish");
    setMutating(true);
    try {
      const result = (await publishListing(token, seedInt, deterministicRunId, walletAddress, sku, title, px)) as RunResult;
      setLastAction(result);
      setToast(t("store.listingPublished", { runId: deterministicRunId }));
      setShowPublish(false);
      setPublishSku("");
      setPublishTitle("");
      setPublishPrice("10");
      await refreshAll();
    } catch (err) {
      setPublishError(renderApiError(err));
    } finally {
      setMutating(false);
    }
  };

  const handlePurchase = async () => {
    if (!backendOnline || !session || !buyListing) return;
    setBuyError("");
    setToast("");
    setLastAction(null);

    const qty = Number(buyQty);
    if (!Number.isInteger(qty) || qty <= 0) {
      setBuyError(t("store.quantityPositive"));
      return;
    }

    let seedInt = 0;
    try {
      seedInt = parseSeed(seed);
    } catch (err) {
      setBuyError(renderApiError(err));
      return;
    }

    const deterministicRunId = allocateRunId(runId, `marketplace-purchase-${buyListing.listing_id}`);
    setMutating(true);
    try {
      const result = (await purchaseMarketplace(
        token,
        seedInt,
        deterministicRunId,
        walletAddress,
        buyListing.listing_id,
        qty,
      )) as RunResult;
      setLastAction(result);
      setToast(t("store.purchased", { runId: deterministicRunId }));
      setBuyListing(null);
      setBuyQty("1");
      await refreshAll();
      setTab("orders");
    } catch (err) {
      setBuyError(renderApiError(err));
    } finally {
      setMutating(false);
    }
  };

  return (
    <div className="flex flex-col gap-6 pb-24 text-text-main dark:text-white">
      <div className="flex items-center justify-between px-2">
        <div>
          <div className="text-xl font-black tracking-tight">{t("store.title")}</div>
          <div className="text-[10px] text-text-subtle uppercase tracking-widest">{t("store.subtitle")}</div>
        </div>
        <button
          onClick={() => setShowPublish(true)}
          className="text-[10px] font-bold text-primary uppercase tracking-widest"
          disabled={!session}
          title={!session ? t("store.signInRequired") : t("store.publishHint")}
        >
          {t("store.publish")}
        </button>
      </div>

      <div className="flex items-center justify-between gap-3">
        <div className="flex-1 flex items-center gap-2 px-4 py-2 bg-surface-light dark:bg-surface-dark rounded-2xl border border-primary/10">
          <span className="material-symbols-outlined text-[18px] text-text-subtle">search</span>
          <input
            className="flex-1 bg-transparent outline-none text-sm"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t("store.searchPlaceholder")}
          />
        </div>
        <button
          onClick={refreshAll}
          className="px-3 py-2 rounded-2xl bg-primary text-black text-[10px] font-bold uppercase tracking-widest"
          disabled={!backendOnline}
        >
          {t("common.refresh")}
        </button>
      </div>

      <div className="flex items-center justify-between px-1">
        <div className="text-[10px] font-bold text-text-subtle uppercase tracking-widest">
          {t("store.balanceLabel")}{" "}
          {nyxtBalance === null ? (
            <span className="text-text-subtle">—</span>
          ) : (
            <span className="text-primary">{nyxtBalance.toLocaleString()}</span>
          )}
        </div>
        {balanceError && (
          <button onClick={loadBalance} className="text-[10px] font-bold text-binance-red uppercase tracking-widest">
            {t("store.balanceErrorRetry")}
          </button>
        )}
      </div>

      <div className="flex border-b border-primary/10">
        <TabButton active={tab === "shop"} onClick={() => setTab("shop")} label={t("store.tabShop")} />
        <TabButton active={tab === "orders"} onClick={() => setTab("orders")} label={t("store.tabOrders")} />
      </div>

      {tab === "shop" ? (
        <div className="flex flex-col gap-4">
          {listingsError && (
            <div className="text-xs text-binance-red bg-binance-red/10 border border-binance-red/20 px-3 py-2 rounded-xl">
              {listingsError}{" "}
              <button onClick={() => loadListings({ reset: true })} className="underline font-bold">
                {t("common.retry")}
              </button>
            </div>
          )}

          {!listingsError && listings.length === 0 && !listingsLoading && (
            <div className="p-6 rounded-3xl bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5 text-sm text-text-subtle">
              {searchActive ? t("store.noResults") : t("store.noListings")}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            {listings.map((item) => (
              <div
                key={item.listing_id}
                className="flex flex-col rounded-3xl overflow-hidden bg-surface-light dark:bg-surface-dark/40 border border-primary/5 shadow-xl"
              >
                <div className="aspect-square bg-gradient-to-br from-primary/15 to-primary-dark/30 flex items-center justify-center">
                  <span className="material-symbols-outlined text-[56px] text-primary/40">inventory_2</span>
                </div>
                <div className="p-4 flex flex-col gap-2">
                  <div className="text-[10px] text-text-subtle font-medium uppercase tracking-wider">{item.sku}</div>
                  <div className="font-bold text-sm line-clamp-2 min-h-[40px]">{item.title}</div>
                  <div className="flex items-center justify-between mt-2">
                    <div className="flex flex-col">
                      <span className="text-[10px] text-text-subtle">{t("store.price")}</span>
                      <span className="text-primary font-extrabold text-lg">
                        {item.price} <span className="text-xs">NYXT</span>
                      </span>
                    </div>
                    <button
                      onClick={() => setBuyListing(item)}
                      className="size-10 rounded-xl bg-primary text-black flex items-center justify-center hover:scale-105 active:scale-95 transition-all shadow-lg"
                      disabled={!session}
                      title={!session ? t("store.signInRequired") : t("store.buy")}
                    >
                      <span className="material-symbols-outlined text-[18px]">shopping_cart</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {listingsLoading && <div className="text-[10px] text-text-subtle">{t("common.loading")}</div>}
          {!listingsLoading && listingsHasMore && (
            <button
              onClick={() => loadListings()}
              className="w-full py-2 rounded-xl border border-primary/20 text-[10px] font-bold text-primary uppercase tracking-widest"
            >
              {t("common.loadMore")}
            </button>
          )}
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {purchasesError && (
            <div className="text-xs text-binance-red bg-binance-red/10 border border-binance-red/20 px-3 py-2 rounded-xl">
              {purchasesError}{" "}
              <button onClick={() => loadPurchases({ reset: true })} className="underline font-bold">
                {t("common.retry")}
              </button>
            </div>
          )}

          {!purchasesError && purchases.length === 0 && !purchasesLoading && (
            <div className="p-6 rounded-3xl bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5 text-sm text-text-subtle">
              {t("store.noPurchases")}
            </div>
          )}

          <div className="flex flex-col gap-2">
            {purchases.map((p) => (
              <div
                key={p.purchase_id}
                className="p-4 rounded-3xl bg-surface-light dark:bg-surface-dark/20 border border-primary/5"
                >
                <div className="flex items-center justify-between">
                  <div className="text-sm font-bold truncate">{p.title ?? p.sku ?? t("store.purchase")}</div>
                  <div className="text-[10px] text-text-subtle">{t("store.qtyLabel", { qty: p.qty })}</div>
                </div>
                <div className="mt-1 text-[10px] font-mono text-text-subtle break-all">
                  {t("store.purchaseLabel", { id: formatCompactId(p.purchase_id) })}
                </div>
                <div className="mt-1 text-[10px] font-mono text-text-subtle break-all">
                  {t("store.runLabel", { id: p.run_id })}
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <button
                    onClick={() => {
                      try {
                        navigator.clipboard.writeText(p.run_id);
                        setToast(t("store.runIdCopied"));
                      } catch {
                        // ignore
                      }
                    }}
                    className="text-[10px] font-bold text-primary uppercase tracking-widest"
                  >
                    {t("store.copyRunId")}
                  </button>
                  <button
                    onClick={() => onNavigate(Screen.ACTIVITY)}
                    className="text-[10px] font-bold text-primary uppercase tracking-widest"
                  >
                    {t("store.evidenceCenter")}
                  </button>
                </div>
              </div>
            ))}
          </div>

          {purchasesLoading && <div className="text-[10px] text-text-subtle">{t("common.loading")}</div>}
          {!purchasesLoading && purchasesHasMore && (
            <button
              onClick={() => loadPurchases()}
              className="w-full py-2 rounded-xl border border-primary/20 text-[10px] font-bold text-primary uppercase tracking-widest"
            >
              {t("common.loadMore")}
            </button>
          )}
        </div>
      )}

      {showPublish && (
        <Modal title={t("store.publishListingTitle")} onClose={() => setShowPublish(false)}>
          <div className="flex flex-col gap-3">
            <label className="flex flex-col gap-1">
              <span className="text-[10px] font-bold text-text-subtle uppercase">{t("store.sku")}</span>
              <input
                className="h-10 rounded-xl bg-surface-light dark:bg-surface-dark border border-black/5 dark:border-white/5 px-3 text-sm outline-none"
                value={publishSku}
                onChange={(e) => setPublishSku(e.target.value)}
                placeholder={t("store.skuPlaceholder")}
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-[10px] font-bold text-text-subtle uppercase">{t("store.titleLabel")}</span>
              <input
                className="h-10 rounded-xl bg-surface-light dark:bg-surface-dark border border-black/5 dark:border-white/5 px-3 text-sm outline-none"
                value={publishTitle}
                onChange={(e) => setPublishTitle(e.target.value)}
                placeholder={t("store.titlePlaceholder")}
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-[10px] font-bold text-text-subtle uppercase">{t("store.priceNyxt")}</span>
              <input
                className="h-10 rounded-xl bg-surface-light dark:bg-surface-dark border border-black/5 dark:border-white/5 px-3 text-sm outline-none"
                value={publishPrice}
                onChange={(e) => setPublishPrice(e.target.value)}
                inputMode="numeric"
              />
            </label>

            {publishError && (
              <div className="text-xs text-binance-red bg-binance-red/10 border border-binance-red/20 px-3 py-2 rounded-xl">
                {publishError}
              </div>
            )}

            <button
              onClick={handlePublish}
              disabled={mutating}
              className={`w-full py-3 rounded-xl font-bold transition-all active:scale-95 ${
                mutating ? "bg-surface-light dark:bg-surface-dark text-text-subtle" : "bg-primary text-black"
              }`}
            >
              {mutating ? t("store.publishing") : t("store.publishButton")}
            </button>
          </div>
        </Modal>
      )}

      {buyListing && (
        <Modal title={t("store.confirmPurchase")} onClose={() => setBuyListing(null)}>
          <div className="flex flex-col gap-3">
            <div className="text-sm font-bold">{buyListing.title}</div>
            <div className="text-xs text-text-subtle">
              {t("store.priceEach", { price: buyListing.price })} • {t("store.sellerLabel")}{" "}
              {formatCompactId(buyListing.publisher_id)}
            </div>
            <label className="flex flex-col gap-1">
              <span className="text-[10px] font-bold text-text-subtle uppercase">{t("store.quantity")}</span>
              <input
                className="h-10 rounded-xl bg-surface-light dark:bg-surface-dark border border-black/5 dark:border-white/5 px-3 text-sm outline-none"
                value={buyQty}
                onChange={(e) => setBuyQty(e.target.value)}
                inputMode="numeric"
              />
            </label>

            {buyError && (
              <div className="text-xs text-binance-red bg-binance-red/10 border border-binance-red/20 px-3 py-2 rounded-xl">
                {buyError}
              </div>
            )}

            <button
              onClick={handlePurchase}
              disabled={mutating}
              className={`w-full py-3 rounded-xl font-bold transition-all active:scale-95 ${
                mutating ? "bg-surface-light dark:bg-surface-dark text-text-subtle" : "bg-primary text-black"
              }`}
            >
              {mutating ? t("store.purchasing") : t("store.buyNow")}
            </button>
          </div>
        </Modal>
      )}

      {lastAction && (
        <div className="p-4 rounded-2xl bg-black/5 dark:bg-white/5 border border-black/5 dark:border-white/10">
          <div className="text-[10px] font-bold text-text-subtle uppercase mb-1">{t("common.lastAction")}</div>
          <div className="text-[10px] font-mono text-text-subtle break-all">
            {t("common.runId")}: {String(lastAction.run_id ?? "")}
          </div>
          <div className="text-[10px] font-mono text-text-subtle break-all">
            {t("common.stateHash")}: {String(lastAction.state_hash ?? "")}
          </div>
          <div className="text-[10px] text-text-subtle">
            {t("activity.feeTotal")} {String(lastAction.fee_total ?? "—")} • {t("activity.treasury")}{" "}
            {String(lastAction.treasury_address ?? "—")}
          </div>
        </div>
      )}

      {toast && (
        <div className="fixed bottom-24 left-1/2 -translate-x-1/2 px-4 py-2 rounded-xl bg-primary text-black text-xs font-bold shadow-2xl animate-in slide-in-from-bottom-2">
          {toast}
        </div>
      )}
    </div>
  );
};

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
