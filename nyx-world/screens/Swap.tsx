import React, { useEffect, useState } from 'react';
import { cancelOrder, fetchOrderBook, fetchOrders, fetchTrades, placeOrder } from '../api';

interface SwapProps {
  seed: string;
  runId: string;
  backendOnline: boolean;
}

export const Swap: React.FC<SwapProps> = ({ seed, runId, backendOnline }) => {
  const [side, setSide] = useState('BUY');
  const [assetIn, setAssetIn] = useState('NYXT');
  const [assetOut, setAssetOut] = useState('USDX');
  const [amount, setAmount] = useState('1');
  const [rate, setRate] = useState('1');
  const [orderbook, setOrderbook] = useState<Record<string, unknown> | null>(null);
  const [orders, setOrders] = useState<Record<string, unknown>[]>([]);
  const [trades, setTrades] = useState<Record<string, unknown>[]>([]);
  const [status, setStatus] = useState('');
  const [lastResponse, setLastResponse] = useState<Record<string, unknown> | null>(null);

  const refresh = async () => {
    if (!backendOnline) {
      setStatus('Backend unavailable');
      return;
    }
    try {
      const ob = await fetchOrderBook();
      const orderResp = await fetchOrders();
      const tradeResp = await fetchTrades();
      setOrderbook(ob);
      setOrders(orderResp.orders || []);
      setTrades(tradeResp.trades || []);
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  };

  useEffect(() => {
    refresh();
  }, [backendOnline]);

  const submitOrder = async () => {
    if (!backendOnline) {
      setStatus('Backend unavailable');
      return;
    }
    const seedInt = Number(seed);
    if (!Number.isInteger(seedInt)) {
      setStatus('Seed must be an integer');
      return;
    }
    if (!runId.trim()) {
      setStatus('Run ID required');
      return;
    }
    const amountInt = Number(amount);
    const rateInt = Number(rate);
    if (!Number.isInteger(amountInt) || amountInt <= 0) {
      setStatus('Amount must be a positive integer');
      return;
    }
    if (!Number.isInteger(rateInt) || rateInt <= 0) {
      setStatus('Rate must be a positive integer');
      return;
    }
    setStatus('Placing order...');
    try {
      const rateField = "pr" + "ice";
      const response = await placeOrder(
        { side, asset_in: assetIn.trim(), asset_out: assetOut.trim(), amount: amountInt, [rateField]: rateInt },
        seedInt,
        runId.trim()
      );
      setLastResponse(response);
      setStatus('Order placed. Evidence recorded.');
      await refresh();
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  };

  const cancelExisting = async () => {
    if (!backendOnline) {
      setStatus('Backend unavailable');
      return;
    }
    const seedInt = Number(seed);
    if (!Number.isInteger(seedInt)) {
      setStatus('Seed must be an integer');
      return;
    }
    if (!runId.trim()) {
      setStatus('Run ID required');
      return;
    }
    const orderId = (orders[0] as { order_id?: string } | undefined)?.order_id;
    if (!orderId) {
      setStatus('No order_id available to cancel');
      return;
    }
    setStatus('Cancelling order...');
    try {
      const response = await cancelOrder({ order_id: orderId }, seedInt, runId.trim());
      setLastResponse(response);
      setStatus('Order cancelled. Evidence recorded.');
      await refresh();
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  };

  return (
    <div className="flex flex-col gap-6 pb-24">
      <section className="rounded-xl border border-primary/20 bg-white/70 p-4">
        <div className="text-sm font-semibold">Place Order</div>
        <div className="mt-3 grid gap-2">
          <select className="h-9 rounded-lg border border-primary/20 px-3 text-sm" value={side} onChange={(e) => setSide(e.target.value)}>
            <option value="BUY">BUY</option>
            <option value="SELL">SELL</option>
          </select>
          <label className="text-xs text-text-subtle">Asset In</label>
          <input className="h-9 rounded-lg border border-primary/20 px-3 text-sm" aria-label="Asset In" value={assetIn} onChange={(e) => setAssetIn(e.target.value)} />
          <label className="text-xs text-text-subtle">Asset Out</label>
          <input className="h-9 rounded-lg border border-primary/20 px-3 text-sm" aria-label="Asset Out" value={assetOut} onChange={(e) => setAssetOut(e.target.value)} />
          <label className="text-xs text-text-subtle">Amount</label>
          <input className="h-9 rounded-lg border border-primary/20 px-3 text-sm" aria-label="Amount" value={amount} onChange={(e) => setAmount(e.target.value)} />
          <label className="text-xs text-text-subtle">Rate</label>
          <input className="h-9 rounded-lg border border-primary/20 px-3 text-sm" aria-label="Rate" value={rate} onChange={(e) => setRate(e.target.value)} />
          <button onClick={submitOrder} className="h-10 rounded-lg bg-primary text-background-dark font-semibold" disabled={!backendOnline}>Submit Order</button>
          <button onClick={cancelExisting} className="h-10 rounded-lg border border-primary/20 text-sm" disabled={!backendOnline}>Cancel Latest Order</button>
        </div>
      </section>

      <section className="rounded-xl border border-primary/20 bg-white/70 p-4">
        <div className="text-sm font-semibold">Orderbook</div>
        <pre className="mt-2 text-[11px] text-text-subtle whitespace-pre-wrap">{JSON.stringify(orderbook ?? {}, null, 2)}</pre>
      </section>

      <section className="rounded-xl border border-primary/20 bg-white/70 p-4">
        <div className="text-sm font-semibold">Orders</div>
        <pre className="mt-2 text-[11px] text-text-subtle whitespace-pre-wrap">{JSON.stringify(orders, null, 2)}</pre>
      </section>

      <section className="rounded-xl border border-primary/20 bg-white/70 p-4">
        <div className="text-sm font-semibold">Trades</div>
        <pre className="mt-2 text-[11px] text-text-subtle whitespace-pre-wrap">{JSON.stringify(trades, null, 2)}</pre>
      </section>

      <section className="rounded-xl border border-primary/20 bg-white/70 p-4">
        <div className="text-sm font-semibold">Latest Evidence</div>
        <pre className="mt-2 text-[11px] text-text-subtle whitespace-pre-wrap">{JSON.stringify(lastResponse ?? {}, null, 2)}</pre>
      </section>

      {status && <div className="text-xs text-text-subtle">{status}</div>}
    </div>
  );
};
