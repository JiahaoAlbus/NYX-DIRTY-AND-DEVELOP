import React, { useEffect, useState } from 'react';
import { downloadExportZip, fetchEvidence, fetchActivity, PortalSession } from '../api';
import { formatJson } from '../utils';
import { History, FileJson, Download, ShieldCheck, ArrowRight } from 'lucide-react';

interface ActivityProps {
  runId: string;
  onBack: () => void;
  session: PortalSession | null;
}

export const Activity: React.FC<ActivityProps> = ({ runId, onBack, session }) => {
  const [receipts, setReceipts] = useState<any[]>([]);
  const [selected, setSelected] = useState(runId);
  const [evidence, setEvidence] = useState<Record<string, unknown> | null>(null);
  const [status, setStatus] = useState('');
  const [replaying, setReplaying] = useState(false);
  const [replayResult, setReplayResult] = useState<boolean | null>(null);

  const verifyReplay = async () => {
    if (!selected) return;
    setReplaying(true);
    setReplayResult(null);
    try {
      const payload = await fetchEvidence(selected.trim());
      setReplayResult(payload.replay_ok);
      setEvidence(payload);
    } catch (err) {
      setStatus(`Verification failed: ${(err as Error).message}`);
    } finally {
      setReplaying(false);
    }
  };
  const [loading, setLoading] = useState(false);

  const loadActivity = async () => {
    if (!session) return;
    setLoading(true);
    try {
      const payload = await fetchActivity(session.access_token);
      setReceipts(payload.receipts || []);
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadActivity();
  }, [session]);

  const loadEvidence = async () => {
    if (!selected.trim()) {
      setStatus('Run ID required');
      return;
    }
    try {
      const payload = await fetchEvidence(selected.trim());
      setEvidence(payload);
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  };

  const downloadZip = async () => {
    if (!selected.trim()) {
      setStatus('Run ID required');
      return;
    }
    try {
      const blob = await downloadExportZip(selected.trim());
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${selected.trim()}-export.zip`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  };

  return (
    <div className="flex flex-col gap-6 pb-24 text-text-main dark:text-white">
      <div className="flex items-center justify-between px-2">
        <div className="flex items-center gap-2">
          <History className="text-primary" size={20} />
          <h2 className="text-xl font-black tracking-tight">Recent Activity</h2>
        </div>
        <button onClick={loadActivity} className="text-[10px] font-bold text-primary uppercase tracking-widest">Refresh</button>
      </div>

      <div className="flex flex-col gap-3">
        {receipts.length === 0 ? (
          <div className="p-12 text-center text-text-subtle text-xs bg-surface-light dark:bg-surface-dark/40 rounded-3xl border border-black/5 dark:border-white/5">
            No activity found for this account.
          </div>
        ) : (
          receipts.map((r, i) => (
            <div 
              key={i} 
              onClick={() => setSelected(r.run_id)}
              className={`p-4 rounded-2xl border transition-all cursor-pointer ${selected === r.run_id ? 'bg-primary/10 border-primary shadow-lg scale-[1.02]' : 'bg-surface-light dark:bg-surface-dark/40 border-black/5 dark:border-white/5 hover:border-primary/30'}`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-bold text-primary uppercase">{r.module}:{r.action}</span>
                <span className="text-[10px] font-mono text-text-subtle">{r.run_id}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium">Deterministic Receipt</span>
                <ArrowRight size={12} className="text-text-subtle" />
              </div>
            </div>
          ))
        )}
      </div>

      {selected && (
        <div className="flex flex-col gap-4 p-6 rounded-3xl bg-background-light dark:bg-background-dark border border-primary/20 shadow-2xl animate-in slide-in-from-bottom-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold">Evidence Inspector</h3>
            <div className="flex gap-2">
              <button onClick={loadEvidence} className="p-2 rounded-xl bg-primary text-black hover:scale-105 active:scale-95 transition-all">
                <FileJson size={16} />
              </button>
              <button onClick={downloadZip} className="p-2 rounded-xl border border-primary/20 text-primary hover:scale-105 active:scale-95 transition-all">
                <Download size={16} />
              </button>
            </div>
          </div>
          
          <div className="flex flex-col gap-2 p-4 bg-black/5 dark:bg-white/5 rounded-2xl border border-white/5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-[10px] font-mono text-text-subtle break-all">
                <ShieldCheck size={10} className="text-binance-green" />
                Run: {selected}
              </div>
              <button 
                onClick={verifyReplay}
                disabled={replaying}
                className={`text-[10px] font-bold px-2 py-1 rounded-md transition-all ${replayResult === true ? 'bg-binance-green text-black' : replayResult === false ? 'bg-binance-red text-white' : 'bg-primary text-black'}`}
              >
                {replaying ? 'Verifying...' : replayResult === true ? 'Verified OK' : replayResult === false ? 'Verification Failed' : 'Verify Replay'}
              </button>
            </div>
            {replayResult === true && (
              <div className="text-[10px] text-binance-green font-bold animate-pulse">
                ✨ Deterministic replay successful. State hash matches.
              </div>
            )}
          </div>

          {evidence && (
            <div className="relative group">
              <pre className="p-4 rounded-2xl bg-black text-[#00ff00] text-[10px] font-mono overflow-x-auto max-h-64 no-scrollbar border border-white/10">
                {formatJson(evidence)}
              </pre>
              <div className="absolute top-2 right-2 px-2 py-1 rounded bg-white/10 backdrop-blur-md text-[8px] font-bold text-white uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-opacity">
                Verified Deterministic
              </div>
            </div>
          )}
        </div>
      )}

      {status && (
        <div className="fixed bottom-24 left-1/2 -translate-x-1/2 px-6 py-3 rounded-2xl bg-binance-red text-white text-sm font-bold shadow-2xl">
          {status}
        </div>
      )}
    </div>
  );
};
