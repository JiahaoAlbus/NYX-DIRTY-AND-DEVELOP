import React, { useState } from "react";
import { ArrowUpDown, Landmark, CreditCard, ShieldCheck, ChevronRight } from "lucide-react";

export const Fiat: React.FC = () => {
  const [fiatAmount, setFiatAmount] = useState("100");
  const [cryptoAmount, setCryptoAmount] = useState("100");

  return (
    <div className="flex flex-col gap-6 text-text-main dark:text-white pb-24">
      <div className="flex flex-col gap-2 px-2">
        <h2 className="text-2xl font-bold">Fiat Exchange</h2>
        <p className="text-xs text-text-subtle">Securely swap between Fiat and NYX Testnet assets</p>
      </div>

      <div className="p-6 rounded-3xl glass-dark border border-white/10 flex flex-col gap-4 relative">
        <div className="flex flex-col gap-2 p-4 bg-background-light dark:bg-background-dark/60 rounded-2xl border border-black/5 dark:border-white/5">
          <label className="text-[10px] text-text-subtle uppercase">Pay</label>
          <div className="flex items-center justify-between">
            <input
              className="bg-transparent text-2xl font-bold outline-none flex-1"
              value={fiatAmount}
              onChange={(e) => setFiatAmount(e.target.value)}
            />
            <div className="flex items-center gap-2 bg-surface-light dark:bg-surface-dark px-3 py-1.5 rounded-xl border border-black/5 dark:border-white/5">
              <span className="font-bold text-sm">USD</span>
            </div>
          </div>
        </div>

        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 size-10 rounded-full bg-primary flex items-center justify-center text-black border-4 border-background-dark shadow-xl z-10">
          <ArrowUpDown size={18} />
        </div>

        <div className="flex flex-col gap-2 p-4 bg-background-light dark:bg-background-dark/60 rounded-2xl border border-black/5 dark:border-white/5">
          <label className="text-[10px] text-text-subtle uppercase">Receive</label>
          <div className="flex items-center justify-between">
            <input className="bg-transparent text-2xl font-bold outline-none flex-1" value={cryptoAmount} readOnly />
            <div className="flex items-center gap-2 bg-surface-light dark:bg-surface-dark px-3 py-1.5 rounded-xl border border-black/5 dark:border-white/5">
              <span className="font-bold text-sm">NYXT</span>
            </div>
          </div>
        </div>

        <button className="w-full py-4 rounded-2xl bg-primary text-black font-bold text-lg mt-4 hover:scale-[1.02] active:scale-95 transition-all shadow-xl">
          Buy NYXT
        </button>
      </div>

      <div className="flex flex-col gap-4">
        <h3 className="font-bold px-2 text-sm uppercase text-text-subtle">Payment Methods</h3>
        <div className="flex flex-col gap-3">
          <div className="p-4 rounded-2xl glass bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5 flex items-center justify-between group cursor-pointer hover:bg-surface-light dark:bg-surface-dark/60 transition-all">
            <div className="flex items-center gap-4">
              <div className="size-10 rounded-xl bg-blue-500/20 text-blue-500 flex items-center justify-center">
                <Landmark size={20} />
              </div>
              <div>
                <div className="font-bold text-sm">Bank Transfer</div>
                <div className="text-[10px] text-text-subtle">0% Fee ● 1-3 Business Days</div>
              </div>
            </div>
            <ChevronRight size={18} className="text-text-subtle group-hover:text-text-main dark:text-white" />
          </div>

          <div className="p-4 rounded-2xl glass bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5 flex items-center justify-between group cursor-pointer hover:bg-surface-light dark:bg-surface-dark/60 transition-all">
            <div className="flex items-center gap-4">
              <div className="size-10 rounded-xl bg-orange-500/20 text-orange-500 flex items-center justify-center">
                <CreditCard size={20} />
              </div>
              <div>
                <div className="font-bold text-sm">Credit/Debit Card</div>
                <div className="text-[10px] text-text-subtle">3.5% Fee ● Instant</div>
              </div>
            </div>
            <ChevronRight size={18} className="text-text-subtle group-hover:text-text-main dark:text-white" />
          </div>
        </div>
      </div>

      <div className="mt-auto flex items-center justify-center gap-2 text-[10px] text-text-subtle p-4 bg-primary/5 rounded-2xl border border-primary/10">
        <ShieldCheck size={14} className="text-primary" />
        Security by NYX Deterministic Verification
      </div>
    </div>
  );
};
