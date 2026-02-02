import React, { useState } from 'react';
import { Droplets, Send, Info, ShieldCheck } from 'lucide-react';
import { faucetWallet, PortalSession } from '../api';

export const Faucet: React.FC<{ seed: string, runId: string, backendOnline: boolean, session: PortalSession | null }> = ({ seed, runId, backendOnline, session }) => {
  const [address, setAddress] = useState(session?.account_id ?? '');
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRequest = async () => {
    if (!address.trim() || !backendOnline || !session) return;
    setLoading(true);
    setStatus('Requesting tokens...');
    try {
      await faucetWallet(session.access_token, address.trim(), 1000000000); // 1000 NYXT
      setStatus('1,000 NYXT sent successfully!');
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6 text-text-main dark:text-white pb-24">
      <div className="p-8 rounded-3xl glass-dark border border-white/10 flex flex-col items-center text-center">
        <div className="size-16 rounded-2xl bg-primary/20 flex items-center justify-center text-primary mb-4 shadow-inner">
          <Droplets size={32} />
        </div>
        <h2 className="text-xl font-bold">Testnet Faucet</h2>
        <p className="text-xs text-text-subtle mt-2">Get free testnet tokens for exploration</p>
      </div>

      <div className="p-6 rounded-3xl glass bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5 flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <label className="text-[10px] text-text-subtle uppercase px-1">Wallet Address</label>
          <div className="flex items-center gap-2 px-4 py-3 bg-background-light dark:bg-background-dark rounded-2xl border border-black/5 dark:border-white/5">
            <input 
              className="bg-transparent flex-1 outline-none text-sm font-mono"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
            />
          </div>
        </div>

        <div className="flex flex-col gap-4">
          <div className="p-4 rounded-2xl bg-primary/5 border border-primary/10 flex gap-3 items-start">
            <Info size={16} className="text-primary shrink-0 mt-0.5" />
            <div className="text-[10px] text-text-subtle leading-relaxed">
              Tokens are for testnet use only and have no real-world value. 
              Limit: 1,000 NYXT per 24 hours.
            </div>
          </div>

          <button 
            onClick={handleRequest}
            disabled={loading || !address.trim()}
            className={`w-full py-4 rounded-2xl font-bold flex items-center justify-center gap-2 transition-all ${
              loading || !address.trim() ? 'bg-surface-light dark:bg-surface-dark text-text-subtle' : 'bg-primary text-black hover:scale-[1.02] active:scale-95'
            }`}
          >
            {loading ? <div className="size-4 border-2 border-black/20 border-t-black rounded-full animate-spin" /> : <Send size={18} />}
            Request Tokens
          </button>
        </div>
      </div>

      <div className="flex items-center justify-center gap-2 text-[10px] text-text-subtle">
        <ShieldCheck size={12} /> Secure deterministic execution
      </div>

      {status && (
        <div className="fixed bottom-24 left-1/2 -translate-x-1/2 px-6 py-3 rounded-2xl bg-primary text-black text-sm font-bold shadow-2xl animate-in fade-in slide-in-from-bottom-4">
          {status}
        </div>
      )}
    </div>
  );
};
