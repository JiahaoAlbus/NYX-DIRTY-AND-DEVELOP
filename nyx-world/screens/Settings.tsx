import React from 'react';
import { PortalSession } from '../api';

interface SettingsProps {
  session: PortalSession | null;
  seed: string;
  runId: string;
  onSeedChange: (v: string) => void;
  onRunIdChange: (v: string) => void;
  onLogout: () => void;
}

export const Settings: React.FC<SettingsProps> = ({ session, seed, runId, onSeedChange, onRunIdChange, onLogout }) => {
  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-xl font-bold">Settings</h2>
      
      <div className="flex flex-col gap-4">
        <section className="p-4 rounded-xl bg-white border border-primary/20 shadow-sm">
          <h3 className="text-sm font-bold uppercase text-text-subtle mb-3">Account</h3>
          <div className="flex flex-col gap-2">
            <div className="text-sm font-medium">Handle: @{session?.handle}</div>
            <div className="text-[10px] font-mono break-all text-text-subtle">ID: {session?.account_id}</div>
            <button 
              onClick={onLogout}
              className="mt-2 text-sm font-bold text-red-600 underline text-left"
            >
              Logout / Reset Session
            </button>
          </div>
        </section>

        <section className="p-4 rounded-xl bg-white border border-primary/20 shadow-sm glass">
          <h3 className="text-sm font-bold uppercase text-text-subtle mb-3">Deterministic Run</h3>
          <div className="flex flex-col gap-3">
            <label className="flex flex-col gap-1">
              <span className="text-xs font-medium">Global Seed (Testnet)</span>
              <input 
                className="h-9 rounded-lg border border-primary/20 bg-white/50 px-3 text-sm outline-none focus:border-primary transition-all"
                value={seed}
                onChange={(e) => onSeedChange(e.target.value)}
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs font-medium">Run ID</span>
              <input 
                className="h-9 rounded-lg border border-primary/20 bg-white/50 px-3 text-sm outline-none focus:border-primary transition-all"
                value={runId}
                onChange={(e) => onRunIdChange(e.target.value)}
              />
            </label>
          </div>
          <div className="mt-4 p-3 rounded-xl bg-primary/5 border border-primary/10 text-[10px] text-text-subtle leading-relaxed italic">
            Changing these values will reset the deterministic evidence chain for your next session.
          </div>
        </section>

        <section className="p-4 rounded-xl bg-white border border-primary/20 shadow-sm glass">
          <h3 className="text-sm font-bold uppercase text-text-subtle mb-3">Treasury + Fees</h3>
          <div className="text-xs text-text-subtle leading-relaxed">
            Treasury routing is configured server-side (testnet). Each state mutation response includes{" "}
            <code>fee_total</code> and <code>treasury_address</code>. Use Activity → Evidence Inspector to audit the
            full fee + receipt chain.
          </div>
        </section>

        <section className="p-4 rounded-xl bg-white border border-primary/20 shadow-sm">
          <h3 className="text-sm font-bold uppercase text-text-subtle mb-3">About NYX</h3>
          <div className="text-xs text-text-subtle leading-relaxed">
            NYX is a deterministic, verifiable portal infrastructure. 
            This is a Testnet Portal v1 preview. All state transitions 
            generate evidence that can be replayed for correctness.
          </div>
        </section>
      </div>
    </div>
  );
};
