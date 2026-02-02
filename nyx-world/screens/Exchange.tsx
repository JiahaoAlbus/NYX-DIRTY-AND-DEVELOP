import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType } from 'lightweight-charts';
import { cancelOrder, fetchOrderBook, fetchOrders, fetchTrades, placeOrder, PortalSession } from '../api';
import { TrendingUp, TrendingDown, ArrowUpDown, History } from 'lucide-react';

interface SwapProps {
  seed: string;
  runId: string;
  backendOnline: boolean;
  session: PortalSession | null;
}

export const Exchange: React.FC<SwapProps> = ({ seed, runId, backendOnline, session }) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const [side, setSide] = useState('BUY');
  const [assetIn, setAssetIn] = useState('NYXT');
  const [assetOut, setAssetOut] = useState('USDX');
  const [amount, setAmount] = useState('1');
  const [rate, setRate] = useState('1');
  const [orderbook, setOrderbook] = useState<{ buy: any[]; sell: any[] }>({ buy: [], sell: [] });
  const [orders, setOrders] = useState<any[]>([]);
  const [trades, setTrades] = useState<any[]>([]);
  const [status, setStatus] = useState('');

  const refresh = async () => {
    if (!backendOnline) return;
    try {
      const ob = await fetchOrderBook() as any;
      const orderResp = await fetchOrders();
      const tradeResp = await fetchTrades();
      setOrderbook(ob);
      setOrders(orderResp.orders || []);
      setTrades(tradeResp.trades || []);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 5000);
    return () => clearInterval(timer);
  }, [backendOnline]);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    let chart: any = null;

    // Use a small timeout to ensure the container is correctly sized
    const timer = setTimeout(() => {
      if (!chartContainerRef.current) return;
      
      try {
        chart = createChart(chartContainerRef.current, {
          layout: {
            background: { type: ColorType.Solid, color: 'transparent' },
            textColor: '#707A8A',
          },
          grid: {
            vertLines: { color: 'rgba(70, 74, 83, 0.1)' },
            horzLines: { color: 'rgba(70, 74, 83, 0.1)' },
          },
          width: chartContainerRef.current.clientWidth || 600,
          height: 300,
        });

        if (chart && typeof chart.addCandlestickSeries === 'function') {
          const candleSeries = chart.addCandlestickSeries({
            upColor: '#0ECB81',
            downColor: '#F6465D',
            borderVisible: false,
            wickUpColor: '#0ECB81',
            wickDownColor: '#F6465D',
          });

          // Chart data
          const data = [
            { time: '2024-01-01', open: 10, high: 12, low: 9, close: 11 },
            { time: '2024-01-02', open: 11, high: 15, low: 10, close: 14 },
            { time: '2024-01-03', open: 14, high: 16, low: 13, close: 15 },
            { time: '2024-01-04', open: 15, high: 15, low: 12, close: 13 },
            { time: '2024-01-05', open: 13, high: 14, low: 11, close: 12 },
          ];
          candleSeries.setData(data as any);
        }
      } catch (err) {
        console.error('Error creating chart:', err);
      }
    }, 100);

    const handleResize = () => {
      if (chart && chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    window.addEventListener('resize', handleResize);
    return () => {
      clearTimeout(timer);
      window.removeEventListener('resize', handleResize);
      if (chart) chart.remove();
    };
  }, []);

  const handlePlaceOrder = async () => {
    if (!backendOnline || !session) return;
    setStatus('Placing order...');
    try {
      await placeOrder(
        session.access_token,
        session.account_id,
        side as 'BUY' | 'SELL',
        Number(amount),
        Number(rate),
        assetIn,
        assetOut
      );
      setStatus('Order placed!');
      refresh();
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  };

  return (
    <div className="flex flex-col gap-4 pb-24 text-text-main dark:text-white">
      {/* Header */}
      <div className="flex items-center justify-between p-4 glass-dark rounded-2xl">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold">{assetIn}/{assetOut}</span>
            <span className="text-binance-green text-sm">+2.45%</span>
          </div>
          <div className="hidden sm:flex gap-4 text-xs text-text-subtle">
            <div>24h High: <span className="text-text-main dark:text-white">1.24</span></div>
            <div>24h Low: <span className="text-text-main dark:text-white">0.98</span></div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left: Order Book */}
        <div className="lg:col-span-3 flex flex-col gap-2 glass-dark p-4 rounded-2xl min-h-[400px]">
          <div className="text-xs font-bold text-text-subtle uppercase mb-2">Order Book</div>
          <div className="flex justify-between text-[10px] text-text-subtle mb-1">
            <span>Rate({assetOut})</span>
            <span>Amount({assetIn})</span>
          </div>
          <div className="flex flex-col gap-1 overflow-hidden">
            {orderbook.sell.slice(0, 10).reverse().map((o, i) => (
              <div key={i} className="flex justify-between text-xs py-0.5 relative">
                <span className="text-binance-red z-10">{o.rate}</span>
                <span className="z-10">{o.amount}</span>
                <div className="absolute right-0 top-0 bottom-0 bg-binance-red/10" style={{ width: `${Math.min(o.amount * 10, 100)}%` }} />
              </div>
            ))}
            <div className="py-2 text-center text-lg font-bold border-y border-black/5 dark:border-white/5 my-1">
              {orderbook.sell[0]?.rate ?? '1.00'}
            </div>
            {orderbook.buy.slice(0, 10).map((o, i) => (
              <div key={i} className="flex justify-between text-xs py-0.5 relative">
                <span className="text-binance-green z-10">{o.rate}</span>
                <span className="z-10">{o.amount}</span>
                <div className="absolute right-0 top-0 bottom-0 bg-binance-green/10" style={{ width: `${Math.min(o.amount * 10, 100)}%` }} />
              </div>
            ))}
          </div>
        </div>

        {/* Center: Chart */}
        <div className="lg:col-span-6 flex flex-col gap-4">
          <div className="glass-dark p-4 rounded-2xl">
            <div ref={chartContainerRef} className="w-full" />
          </div>
          
          {/* Recent Trades */}
          <div className="glass-dark p-4 rounded-2xl flex-1">
            <div className="text-xs font-bold text-text-subtle uppercase mb-4 flex items-center gap-2">
              <History size={14} /> Market Trades
            </div>
            <div className="flex flex-col gap-2">
              {trades.slice(0, 5).map((t, i) => (
                <div key={i} className="flex justify-between text-xs">
                  <span className={t.side === 'BUY' ? 'text-binance-green' : 'text-binance-red'}>{t.rate}</span>
                  <span>{t.amount}</span>
                  <span className="text-text-subtle">12:00:01</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Trading Form */}
        <div className="lg:col-span-3 flex flex-col gap-4 glass-dark p-4 rounded-2xl">
          <div className="flex p-1 bg-surface-light dark:bg-surface-dark rounded-xl">
            <button 
              onClick={() => setSide('BUY')}
              className={`flex-1 py-2 rounded-lg text-sm font-bold transition-all ${side === 'BUY' ? 'bg-binance-green text-text-main dark:text-white' : 'text-text-subtle'}`}
            >
              Buy
            </button>
            <button 
              onClick={() => setSide('SELL')}
              className={`flex-1 py-2 rounded-lg text-sm font-bold transition-all ${side === 'SELL' ? 'bg-binance-red text-text-main dark:text-white' : 'text-text-subtle'}`}
            >
              Sell
            </button>
          </div>

          <div className="flex flex-col gap-4 mt-2">
            <div className="flex flex-col gap-1">
              <label className="text-[10px] text-text-subtle uppercase px-1">Rate</label>
              <div className="flex items-center gap-2 px-3 py-2 bg-surface-light dark:bg-surface-dark rounded-xl border border-black/5 dark:border-white/5">
                <input 
                  className="bg-transparent flex-1 outline-none text-sm"
                  value={rate}
                  onChange={(e) => setRate(e.target.value)}
                />
                <span className="text-[10px] text-text-subtle">{assetOut}</span>
              </div>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-[10px] text-text-subtle uppercase px-1">Amount</label>
              <div className="flex items-center gap-2 px-3 py-2 bg-surface-light dark:bg-surface-dark rounded-xl border border-black/5 dark:border-white/5">
                <input 
                  className="bg-transparent flex-1 outline-none text-sm"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                />
                <span className="text-[10px] text-text-subtle">{assetIn}</span>
              </div>
            </div>

            <button 
              onClick={handlePlaceOrder}
              className={`w-full py-3 rounded-xl font-bold mt-2 transition-all active:scale-95 ${
                side === 'BUY' ? 'bg-binance-green' : 'bg-binance-red'
              }`}
            >
              {side} {assetIn}
            </button>

            <div className="mt-4 pt-4 border-t border-black/5 dark:border-white/5">
              <div className="flex justify-between text-xs text-text-subtle">
                <span>Fee (Est.)</span>
                <span className="text-text-main dark:text-white">0.10 %</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {status && (
        <div className="fixed bottom-24 right-6 px-4 py-2 rounded-xl bg-primary text-black text-xs font-bold shadow-2xl animate-in slide-in-from-right">
          {status}
        </div>
      )}
    </div>
  );
};
