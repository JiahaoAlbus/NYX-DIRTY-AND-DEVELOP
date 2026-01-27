import React, { useEffect, useState } from 'react';
import { listEntertainmentEvents, listEntertainmentItems, postEntertainmentStep } from '../api';

interface HomeProps {
  backendOnline: boolean;
  backendStatus: string;
  capabilities: Record<string, unknown> | null;
  onRefresh: () => void;
  seed: string;
  runId: string;
}

export const Home: React.FC<HomeProps> = ({ backendOnline, backendStatus, capabilities, onRefresh, seed, runId }) => {
  const [items, setItems] = useState<Record<string, unknown>[]>([]);
  const [events, setEvents] = useState<Record<string, unknown>[]>([]);
  const [status, setStatus] = useState('');
  const [itemId, setItemId] = useState('');
  const [mode, setMode] = useState('view');
  const [step, setStep] = useState('0');

  const refreshItems = async () => {
    if (!backendOnline) return;
    try {
      const payload = await listEntertainmentItems();
      setItems((payload.items as Record<string, unknown>[]) || []);
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  };

  const refreshEvents = async () => {
    if (!backendOnline) return;
    try {
      const payload = await listEntertainmentEvents();
      setEvents((payload.events as Record<string, unknown>[]) || []);
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  };

  useEffect(() => {
    refreshItems();
    refreshEvents();
  }, [backendOnline]);

  const runStep = async () => {
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
    if (!itemId.trim()) {
      setStatus('item_id required');
      return;
    }
    const stepInt = Number(step);
    if (!Number.isInteger(stepInt) || stepInt < 0) {
      setStatus('Step must be a non-negative integer');
      return;
    }
    setStatus('Submitting entertainment step...');
    try {
      await postEntertainmentStep({ item_id: itemId.trim(), mode: mode.trim(), step: stepInt }, seedInt, runId.trim());
      await refreshEvents();
      setStatus('Step complete. Evidence recorded.');
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  };

  return (
    <div className="flex flex-col gap-6 pb-32">
      <section className="rounded-xl border border-primary/20 bg-white/70 p-4">
        <div className="text-sm font-semibold">Backend status</div>
        <div className="text-xs text-text-subtle">{backendStatus}</div>
        <button onClick={onRefresh} className="mt-2 text-xs font-semibold text-primary underline">Refresh</button>
      </section>

      <section className="rounded-xl border border-primary/20 bg-white/70 p-4">
        <div className="text-sm font-semibold">Capabilities</div>
        <pre className="mt-2 text-[11px] text-text-subtle whitespace-pre-wrap">{JSON.stringify(capabilities || {}, null, 2)}</pre>
      </section>

      <section className="rounded-xl border border-primary/20 bg-white/70 p-4">
        <div className="text-sm font-semibold">Entertainment Items</div>
        <pre className="mt-2 text-[11px] text-text-subtle whitespace-pre-wrap">{JSON.stringify(items, null, 2)}</pre>
      </section>

      <section className="rounded-xl border border-primary/20 bg-white/70 p-4">
        <div className="text-sm font-semibold">Submit Entertainment Step</div>
        <div className="mt-3 grid gap-2">
          <label className="text-xs text-text-subtle">Item ID</label>
          <input className="h-9 rounded-lg border border-primary/20 px-3 text-sm" aria-label="Item ID" value={itemId} onChange={(e) => setItemId(e.target.value)} />
          <label className="text-xs text-text-subtle">Mode</label>
          <input className="h-9 rounded-lg border border-primary/20 px-3 text-sm" aria-label="Mode" value={mode} onChange={(e) => setMode(e.target.value)} />
          <label className="text-xs text-text-subtle">Step</label>
          <input className="h-9 rounded-lg border border-primary/20 px-3 text-sm" aria-label="Step" value={step} onChange={(e) => setStep(e.target.value)} />
          <button className="h-10 rounded-lg bg-primary text-background-dark font-semibold" onClick={runStep} disabled={!backendOnline}>Run Step</button>
        </div>
      </section>

      <section className="rounded-xl border border-primary/20 bg-white/70 p-4">
        <div className="text-sm font-semibold">Entertainment Events</div>
        <pre className="mt-2 text-[11px] text-text-subtle whitespace-pre-wrap">{JSON.stringify(events, null, 2)}</pre>
      </section>

      {status && <div className="text-xs text-text-subtle">{status}</div>}
    </div>
  );
};
