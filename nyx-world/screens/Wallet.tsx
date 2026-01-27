import React, { useState } from 'react';
import { fetchWalletBalance, faucetV1, transferV1, PortalSession } from '../api';
import { Screen } from '../types';

interface WalletProps {
  seed: string;
  runId: string;
  backendOnline: boolean;
  session: PortalSession | null;
  onNavigate: (screen: Screen) => void;
}

export const Wallet: React.FC<WalletProps> = ({ seed, runId, backendOnline, session, onNavigate }) => {
  const [address, setAddress] = useState(session?.account_id ?? '');
  const [balance, setBalance] = useState<number | null>(null);
  const [amount, setAmount] = useState('');
  const [toAddress, setToAddress] = useState('');
  const [status, setStatus] = useState('');
  const [evidence, setEvidence] = useState<Record<string, unknown> | null>(null);

  const loadBalance = async () => {
    if (!backendOnline) {
      setStatus('Backend unavailable');
      return;
    }
    if (!address.trim()) {
      setStatus('Address required');
      return;
    }
    try {
      const payload = await fetchWalletBalance(address.trim());
      setBalance(payload.balance);
      setStatus('Balance refreshed');
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  };

  const runFaucet = async () => {
    if (!backendOnline) {
      setStatus('Backend unavailable');
      return;
    }
    if (!session) {
      setStatus('Portal sign-in required');
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
    if (!address.trim()) {
      setStatus('Address required');
      return;
    }
    const amountInt = Number(amount);
    if (!Number.isInteger(amountInt) || amountInt <= 0) {
      setStatus('Amount must be a positive integer');
      return;
    }
    setStatus('Requesting faucet...');
    try {
      const payload = await faucetV1(session.access_token, { address: address.trim(), amount: amountInt }, seedInt, runId.trim());
      setEvidence(payload);
      setStatus('Faucet completed. Evidence ready.');
      await loadBalance();
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  };

  const runTransfer = async () => {
    if (!backendOnline) {
      setStatus('Backend unavailable');
      return;
    }
    if (!session) {
      setStatus('Portal sign-in required');
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
    if (!address.trim() || !toAddress.trim()) {
      setStatus('Both from and to addresses required');
      return;
    }
    const amountInt = Number(amount);
    if (!Number.isInteger(amountInt) || amountInt <= 0) {
      setStatus('Amount must be a positive integer');
      return;
    }
    setStatus('Submitting transfer...');
    try {
      const payload = await transferV1(
        session.access_token,
        { from_address: address.trim(), to_address: toAddress.trim(), amount: amountInt },
        seedInt,
        runId.trim()
      );
      setEvidence(payload);
      setStatus('Transfer completed. Evidence ready.');
      await loadBalance();
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  };

  return (
    <div className="flex flex-col gap-6 pb-32">
      <section className="rounded-xl border border-primary/20 bg-white/70 p-4">
        <div className="text-sm font-semibold">Wallet Address</div>
        <input className="mt-2 h-9 w-full rounded-lg border border-primary/20 px-3 text-sm" value={address} onChange={(e) => setAddress(e.target.value)} />
        <button onClick={loadBalance} className="mt-3 h-10 w-full rounded-lg bg-primary text-background-dark font-semibold" disabled={!backendOnline}>Refresh Balance</button>
        <div className="mt-2 text-sm">Balance: {balance ?? '—'} NYXT</div>
      </section>

      <section className="rounded-xl border border-primary/20 bg-white/70 p-4">
        <div className="text-sm font-semibold">Faucet (Testnet only)</div>
        <label className="mt-2 text-xs text-text-subtle">Amount</label>
        <input className="mt-2 h-9 w-full rounded-lg border border-primary/20 px-3 text-sm" aria-label="Amount" value={amount} onChange={(e) => setAmount(e.target.value)} />
        <button onClick={runFaucet} className="mt-3 h-10 w-full rounded-lg bg-primary text-background-dark font-semibold" disabled={!backendOnline}>Request Faucet</button>
      </section>

      <section className="rounded-xl border border-primary/20 bg-white/70 p-4">
        <div className="text-sm font-semibold">Transfer</div>
        <label className="mt-2 text-xs text-text-subtle">To address</label>
        <input className="mt-2 h-9 w-full rounded-lg border border-primary/20 px-3 text-sm" aria-label="To address" value={toAddress} onChange={(e) => setToAddress(e.target.value)} />
        <label className="mt-2 text-xs text-text-subtle">Amount</label>
        <input className="mt-2 h-9 w-full rounded-lg border border-primary/20 px-3 text-sm" aria-label="Amount" value={amount} onChange={(e) => setAmount(e.target.value)} />
        <button onClick={runTransfer} className="mt-3 h-10 w-full rounded-lg bg-primary text-background-dark font-semibold" disabled={!backendOnline}>Submit Transfer</button>
      </section>

      <section className="rounded-xl border border-primary/20 bg-white/70 p-4">
        <div className="text-sm font-semibold">Evidence Snapshot</div>
        <pre className="mt-2 text-[11px] text-text-subtle whitespace-pre-wrap">{JSON.stringify(evidence ?? {}, null, 2)}</pre>
        <button onClick={() => onNavigate(Screen.ACTIVITY)} className="mt-2 text-xs font-semibold text-primary underline">Open Evidence Center</button>
      </section>

      {status && <div className="text-xs text-text-subtle">{status}</div>}
    </div>
  );
};
