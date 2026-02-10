import React, { useEffect, useMemo, useState } from "react";
import {
  allocateRunId,
  ApiError,
  cancelOrder,
  fetchMyOrdersV1,
  fetchMyTradesV1,
  fetchOrderBook,
  parseSeed,
  placeOrder,
  PortalSession,
} from "../api";
import { Screen } from "../types";
import { useI18n } from "../i18n";
import { getStoredLocale, translate } from "../i18nCore";

type OrderRow = {
  order_id: string;
  owner_address: string;
  side: "BUY" | "SELL";
  amount: number;
  price: number;
  asset_in: string;
  asset_out: string;
  status: "open" | "filled" | "cancelled";
  run_id: string;
  state_hash?: string;
  receipt_hashes?: string[];
  replay_ok?: boolean;
};

type TradeRow = {
  trade_id: string;
  order_id: string;
  amount: number;
  price: number;
  run_id: string;
  side: "BUY" | "SELL";
  asset_in: string;
  asset_out: string;
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

interface ExchangeProps {
  seed: string;
  runId: string;
  backendOnline: boolean;
  session: PortalSession | null;
  onNavigate: (screen: Screen) => void;
}

const ORDERBOOK_LIMIT = 25;
const PAGE_LIMIT = 25;

function formatCompactId(value: string): string {
  const v = (value || "").trim();
  if (v.length <= 18) return v;
  return `${v.slice(0, 10)}…${v.slice(-6)}`;
}

function renderApiError(err: unknown): string {
  const locale = getStoredLocale();
  if (err instanceof ApiError) {
    const parts = [err.message];
    if (err.code && !err.message.includes(err.code)) parts.push(`(${err.code})`);
    const retryAfter = err.details?.retry_after_seconds;
    if (typeof retryAfter === "number" && Number.isFinite(retryAfter)) {
      parts.push(translate("common.retryAfter", { seconds: retryAfter }, locale));
    }
    return parts.join(" ");
  }
  return (err as Error)?.message ?? translate("common.unknownError", undefined, locale);
}

export const Exchange: React.FC<ExchangeProps> = ({ seed, runId, backendOnline, session, onNavigate }) => {
  const { t } = useI18n();
  const token = session?.access_token ?? "";
  const walletAddress = session?.wallet_address ?? "";

  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const assetIn = useMemo(() => (side === "BUY" ? "NYXT" : "ECHO"), [side]);
  const assetOut = useMemo(() => (side === "BUY" ? "ECHO" : "NYXT"), [side]);

  const [amount, setAmount] = useState("100");
  const [price, setPrice] = useState("10");

  const [orderbook, setOrderbook] = useState<{ buy: OrderRow[]; sell: OrderRow[] }>({ buy: [], sell: [] });
  const [obLoading, setObLoading] = useState(false);
  const [obError, setObError] = useState("");

  const [ordersStatus, setOrdersStatus] = useState<"open" | "filled" | "cancelled" | "all">("open");
  const [orders, setOrders] = useState<OrderRow[]>([]);
  const [ordersLoading, setOrdersLoading] = useState(false);
  const [ordersError, setOrdersError] = useState("");
  const [ordersOffset, setOrdersOffset] = useState(0);
  const [ordersHasMore, setOrdersHasMore] = useState(true);

  const [trades, setTrades] = useState<TradeRow[]>([]);
  const [tradesLoading, setTradesLoading] = useState(false);
  const [tradesError, setTradesError] = useState("");
  const [tradesOffset, setTradesOffset] = useState(0);
  const [tradesHasMore, setTradesHasMore] = useState(true);

  const [mutating, setMutating] = useState(false);
  const [actionError, setActionError] = useState("");
  const [toast, setToast] = useState("");
  const [lastAction, setLastAction] = useState<RunResult | null>(null);

  const loadOrderbook = async () => {
    if (!backendOnline) return;
    setObLoading(true);
    setObError("");
    try {
      const payload = (await fetchOrderBook(ORDERBOOK_LIMIT, 0)) as any;
      setOrderbook({
        buy: (payload.buy as OrderRow[]) || [],
        sell: (payload.sell as OrderRow[]) || [],
      });
    } catch (err) {
      setObError(renderApiError(err));
    } finally {
      setObLoading(false);
    }
  };

  const loadOrders = async (opts?: { reset?: boolean }) => {
    if (!backendOnline || !session) return;
    setOrdersLoading(true);
    setOrdersError("");
    try {
      const nextOffset = opts?.reset ? 0 : ordersOffset;
      const payload = await fetchMyOrdersV1(token, ordersStatus, PAGE_LIMIT, nextOffset);
      const list = (payload.orders as OrderRow[]) || [];
      if (opts?.reset) setOrders(list);
      else setOrders((prev) => [...prev, ...list]);
      setOrdersHasMore(list.length === PAGE_LIMIT);
      setOrdersOffset(nextOffset + list.length);
    } catch (err) {
      setOrdersError(renderApiError(err));
    } finally {
      setOrdersLoading(false);
    }
  };

  const loadTrades = async (opts?: { reset?: boolean }) => {
    if (!backendOnline || !session) return;
    setTradesLoading(true);
    setTradesError("");
    try {
      const nextOffset = opts?.reset ? 0 : tradesOffset;
      const payload = await fetchMyTradesV1(token, PAGE_LIMIT, nextOffset);
      const list = (payload.trades as TradeRow[]) || [];
      if (opts?.reset) setTrades(list);
      else setTrades((prev) => [...prev, ...list]);
      setTradesHasMore(list.length === PAGE_LIMIT);
      setTradesOffset(nextOffset + list.length);
    } catch (err) {
      setTradesError(renderApiError(err));
    } finally {
      setTradesLoading(false);
    }
  };

  const refreshAll = async () => {
    await loadOrderbook();
    await loadOrders({ reset: true });
    await loadTrades({ reset: true });
  };

  useEffect(() => {
    refreshAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [backendOnline, session?.access_token, session?.wallet_address]);

  useEffect(() => {
    if (!session) return;
    loadOrders({ reset: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ordersStatus]);

  const handlePlaceOrder = async () => {
    if (!backendOnline || !session) return;
    setActionError("");
    setToast("");
    setLastAction(null);

    let seedInt = 0;
    try {
      seedInt = parseSeed(seed);
    } catch (err) {
      setActionError(renderApiError(err));
      return;
    }

    const amt = Number(amount);
    const px = Number(price);
    if (!Number.isInteger(amt) || amt <= 0) {
      setActionError(t("exchange.amountPositive"));
      return;
    }
    if (!Number.isInteger(px) || px <= 0) {
      setActionError(t("exchange.pricePositive"));
      return;
    }

    const deterministicRunId = allocateRunId(runId, "exchange-place-order");
    setMutating(true);
    try {
      const result = (await placeOrder(
        token,
        seedInt,
        deterministicRunId,
        walletAddress,
        side,
        amt,
        px,
        assetIn,
        assetOut,
      )) as RunResult;
      setLastAction(result);
      setToast(t("exchange.orderPlaced", { runId: deterministicRunId }));
      await refreshAll();
    } catch (err) {
      setActionError(renderApiError(err));
    } finally {
      setMutating(false);
    }
  };

  const handleCancelOrder = async (orderId: string) => {
    if (!backendOnline || !session) return;
    setActionError("");
    setToast("");
    setLastAction(null);

    let seedInt = 0;
    try {
      seedInt = parseSeed(seed);
    } catch (err) {
      setActionError(renderApiError(err));
      return;
    }

    const deterministicRunId = allocateRunId(runId, `exchange-cancel-${orderId}`);
    setMutating(true);
    try {
      const result = (await cancelOrder(token, seedInt, deterministicRunId, orderId)) as RunResult;
      setLastAction(result);
      setToast(t("exchange.orderCancelled", { runId: deterministicRunId }));
      await refreshAll();
    } catch (err) {
      setActionError(renderApiError(err));
    } finally {
      setMutating(false);
    }
  };

  const copyText = async (value: string) => {
    try {
      await navigator.clipboard.writeText(value);
      setToast(t("common.copied"));
    } catch {
      // ignore
    }
  };

  return (
    <div className="flex flex-col gap-6 pb-24 text-text-main dark:text-white">
      <div className="flex items-center justify-between px-2">
        <div>
          <div className="text-xl font-black tracking-tight">{t("exchange.title")}</div>
          <div className="text-[10px] text-text-subtle uppercase tracking-widest">{t("exchange.subtitle")}</div>
        </div>
        <button
          onClick={refreshAll}
          className="text-[10px] font-bold text-primary uppercase tracking-widest"
          disabled={!backendOnline}
        >
          {t("common.refresh")}
        </button>
      </div>

      {!session && (
        <div className="p-4 rounded-2xl bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5 text-sm text-text-subtle">
          {t("exchange.signIn")}
        </div>
      )}

      {session && (
        <>
          {/* Order book */}
          <div className="p-4 rounded-2xl bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5">
            <div className="flex items-center justify-between mb-3">
              <div className="text-xs font-bold text-text-subtle uppercase">{t("exchange.orderbook")}</div>
              {obLoading && <div className="text-[10px] text-text-subtle">{t("common.loading")}</div>}
            </div>

            {obError && (
              <div className="mb-3 text-xs text-binance-red bg-binance-red/10 border border-binance-red/20 px-3 py-2 rounded-xl">
                {obError}{" "}
                <button onClick={loadOrderbook} className="underline font-bold">
                  {t("common.retry")}
                </button>
              </div>
            )}

            {!obError && orderbook.buy.length === 0 && orderbook.sell.length === 0 && !obLoading && (
              <div className="text-sm text-text-subtle">{t("exchange.noOrdersYet")}</div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-[10px] font-bold text-text-subtle uppercase mb-2">
                  {t("exchange.sellBook", { asset: "ECHO" })}
                </div>
                <div className="flex flex-col gap-1">
                  {orderbook.sell.slice(0, 10).map((row) => (
                    <div key={row.order_id} className="flex justify-between text-xs font-mono">
                      <span className="text-binance-red">{row.price}</span>
                      <span>{row.amount}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <div className="text-[10px] font-bold text-text-subtle uppercase mb-2">
                  {t("exchange.buyBook", { asset: "NYXT" })}
                </div>
                <div className="flex flex-col gap-1">
                  {orderbook.buy.slice(0, 10).map((row) => (
                    <div key={row.order_id} className="flex justify-between text-xs font-mono">
                      <span className="text-binance-green">{row.price}</span>
                      <span>{row.amount}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-3 text-[10px] text-text-subtle">
              {t("exchange.bookNote")}
            </div>
          </div>

          {/* Place order */}
          <div className="p-4 rounded-2xl bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5">
            <div className="flex items-center justify-between mb-3">
              <div className="text-xs font-bold text-text-subtle uppercase">{t("exchange.placeOrder")}</div>
              <button
                onClick={() => onNavigate(Screen.WALLET)}
                className="text-[10px] font-bold text-primary uppercase tracking-widest"
              >
                {t("nav.wallet")}
              </button>
            </div>

            <div className="flex p-1 bg-surface-light dark:bg-surface-dark rounded-xl border border-black/5 dark:border-white/5">
              <button
                onClick={() => setSide("BUY")}
                className={`flex-1 py-2 rounded-lg text-sm font-bold transition-all ${
                  side === "BUY" ? "bg-binance-green text-black" : "text-text-subtle"
                }`}
              >
                {t("exchange.buy")}
              </button>
              <button
                onClick={() => setSide("SELL")}
                className={`flex-1 py-2 rounded-lg text-sm font-bold transition-all ${
                  side === "SELL" ? "bg-binance-red text-white" : "text-text-subtle"
                }`}
              >
                {t("exchange.sell")}
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 mt-4">
              <label className="flex flex-col gap-1">
                <span className="text-[10px] font-bold text-text-subtle uppercase">
                  {t("exchange.priceLabel", { pair: "NYXT/ECHO" })}
                </span>
                <input
                  className="h-10 rounded-xl bg-surface-light dark:bg-surface-dark border border-black/5 dark:border-white/5 px-3 text-sm outline-none"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  inputMode="numeric"
                />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-[10px] font-bold text-text-subtle uppercase">
                  {t("exchange.amountLabel", { asset: assetIn })}
                </span>
                <input
                  className="h-10 rounded-xl bg-surface-light dark:bg-surface-dark border border-black/5 dark:border-white/5 px-3 text-sm outline-none"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  inputMode="numeric"
                />
              </label>
            </div>

            <button
              onClick={handlePlaceOrder}
              disabled={!backendOnline || mutating}
              className={`mt-4 w-full py-3 rounded-xl font-bold transition-all active:scale-95 ${
                mutating
                  ? "bg-surface-light dark:bg-surface-dark text-text-subtle"
                  : side === "BUY"
                    ? "bg-binance-green text-black"
                    : "bg-binance-red text-white"
              }`}
              title={!backendOnline ? t("app.backendUnavailable") : ""}
            >
              {mutating ? t("exchange.submitting") : `${t(side === "BUY" ? "exchange.buy" : "exchange.sell")} ${assetOut}`}
            </button>

            {actionError && (
              <div className="mt-3 text-xs text-binance-red bg-binance-red/10 border border-binance-red/20 px-3 py-2 rounded-xl">
                {actionError}
              </div>
            )}

            {lastAction && (
              <div className="mt-4 p-3 rounded-xl bg-black/5 dark:bg-white/5 border border-black/5 dark:border-white/10">
                <div className="text-[10px] font-bold text-text-subtle uppercase mb-1">{t("exchange.lastAction")}</div>
                <div className="text-[10px] font-mono text-text-subtle break-all">
                  {t("common.runId")}: {String(lastAction.run_id ?? "")}
                </div>
                <div className="text-[10px] font-mono text-text-subtle break-all">
                  {t("common.stateHash")}: {String(lastAction.state_hash ?? "")}
                </div>
                <div className="text-[10px] text-text-subtle">
                  {t("exchange.feeSummary", {
                    fee: String(lastAction.fee_total ?? "—"),
                    treasury: String(lastAction.treasury_address ?? "—"),
                  })}
                </div>
                <button
                  onClick={() => copyText(String(lastAction.run_id ?? ""))}
                  className="mt-2 text-[10px] font-bold text-primary uppercase tracking-widest"
                >
                  {t("exchange.copyRunId")}
                </button>
              </div>
            )}
          </div>

          {/* My orders */}
          <div className="p-4 rounded-2xl bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5">
            <div className="flex items-center justify-between mb-3">
              <div className="text-xs font-bold text-text-subtle uppercase">{t("exchange.myOrders")}</div>
              <select
                className="text-[10px] bg-surface-light dark:bg-surface-dark border border-black/5 dark:border-white/10 rounded-lg px-2 py-1"
                value={ordersStatus}
                onChange={(e) => setOrdersStatus(e.target.value as any)}
              >
                <option value="open">{t("exchange.statusOpen")}</option>
                <option value="filled">{t("exchange.statusFilled")}</option>
                <option value="cancelled">{t("exchange.statusCancelled")}</option>
                <option value="all">{t("exchange.statusAll")}</option>
              </select>
            </div>

            {ordersError && (
              <div className="mb-3 text-xs text-binance-red bg-binance-red/10 border border-binance-red/20 px-3 py-2 rounded-xl">
                {ordersError}{" "}
                <button onClick={() => loadOrders({ reset: true })} className="underline font-bold">
                  {t("common.retry")}
                </button>
              </div>
            )}

            {!ordersError && orders.length === 0 && !ordersLoading && (
              <div className="text-sm text-text-subtle">{t("exchange.noOrders")}</div>
            )}

            <div className="flex flex-col gap-2">
              {orders.map((o) => (
                <div
                  key={o.order_id}
                  className="p-3 rounded-xl bg-black/5 dark:bg-white/5 border border-black/5 dark:border-white/10"
                >
                  <div className="flex items-center justify-between">
                    <div className="text-xs font-bold">
                      <span className={o.side === "BUY" ? "text-binance-green" : "text-binance-red"}>{o.side}</span>{" "}
                      <span className="text-text-subtle">{o.asset_out}</span>
                    </div>
                    <div className="text-[10px] text-text-subtle">{o.status}</div>
                  </div>
                  <div className="flex items-center justify-between mt-1 text-[10px] font-mono text-text-subtle">
                    <span>{t("exchange.orderLabel", { id: formatCompactId(o.order_id) })}</span>
                    <span>{t("exchange.runLabel", { id: formatCompactId(o.run_id) })}</span>
                  </div>
                  <div className="flex items-center justify-between mt-2 text-xs">
                    <span>
                      {t("exchange.amountShort")} <span className="font-mono">{o.amount}</span> {o.asset_in}
                    </span>
                    <span>
                      {t("exchange.priceShort")} <span className="font-mono">{o.price}</span>
                    </span>
                  </div>
                  <div className="mt-2 flex items-center justify-between">
                    <button
                      onClick={() => copyText(o.run_id)}
                      className="text-[10px] font-bold text-primary uppercase tracking-widest"
                    >
                      {t("exchange.copyRunId")}
                    </button>
                    {o.status === "open" && (
                      <button
                        onClick={() => handleCancelOrder(o.order_id)}
                        className="text-[10px] font-bold text-binance-red uppercase tracking-widest"
                      >
                        {t("common.cancel")}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {ordersLoading && <div className="mt-3 text-[10px] text-text-subtle">{t("common.loading")}</div>}
            {!ordersLoading && ordersHasMore && (
              <button
                onClick={() => loadOrders()}
                className="mt-3 w-full py-2 rounded-xl border border-primary/20 text-[10px] font-bold text-primary uppercase tracking-widest"
              >
                {t("common.loadMore")}
              </button>
            )}
          </div>

          {/* My trades */}
          <div className="p-4 rounded-2xl bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5">
            <div className="flex items-center justify-between mb-3">
              <div className="text-xs font-bold text-text-subtle uppercase">{t("exchange.myTrades")}</div>
              <button
                onClick={() => loadTrades({ reset: true })}
                className="text-[10px] font-bold text-primary uppercase tracking-widest"
              >
                {t("common.refresh")}
              </button>
            </div>

            {tradesError && (
              <div className="mb-3 text-xs text-binance-red bg-binance-red/10 border border-binance-red/20 px-3 py-2 rounded-xl">
                {tradesError}{" "}
                <button onClick={() => loadTrades({ reset: true })} className="underline font-bold">
                  {t("common.retry")}
                </button>
              </div>
            )}

            {!tradesError && trades.length === 0 && !tradesLoading && (
              <div className="text-sm text-text-subtle">{t("exchange.noTrades")}</div>
            )}

            <div className="flex flex-col gap-2">
              {trades.map((trade) => (
                <div
                  key={trade.trade_id}
                  className="p-3 rounded-xl bg-black/5 dark:bg-white/5 border border-black/5 dark:border-white/10"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span
                      className={trade.side === "BUY" ? "text-binance-green font-bold" : "text-binance-red font-bold"}
                    >
                      {trade.side}
                    </span>
                    <span className="text-text-subtle font-mono">{formatCompactId(trade.trade_id)}</span>
                  </div>
                  <div className="mt-1 text-xs">
                    {t("exchange.amountShort")} <span className="font-mono">{trade.amount}</span> •{" "}
                    {t("exchange.priceShort")} <span className="font-mono">{trade.price}</span>
                  </div>
                  <div className="mt-1 text-[10px] font-mono text-text-subtle break-all">
                    {t("common.runShort")}: {trade.run_id}
                  </div>
                </div>
              ))}
            </div>

            {tradesLoading && <div className="mt-3 text-[10px] text-text-subtle">{t("common.loading")}</div>}
            {!tradesLoading && tradesHasMore && (
              <button
                onClick={() => loadTrades()}
                className="mt-3 w-full py-2 rounded-xl border border-primary/20 text-[10px] font-bold text-primary uppercase tracking-widest"
              >
                {t("common.loadMore")}
              </button>
            )}
          </div>
        </>
      )}

      {toast && (
        <div className="fixed bottom-24 left-1/2 -translate-x-1/2 px-4 py-2 rounded-xl bg-primary text-black text-xs font-bold shadow-2xl animate-in slide-in-from-bottom-2">
          {toast}
        </div>
      )}
    </div>
  );
};
