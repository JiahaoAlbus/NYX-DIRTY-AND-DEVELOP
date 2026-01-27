import React, { useState } from 'react';
import { downloadExportZip, fetchEvidence, listEvidenceRuns } from '../api';
import { formatJson } from '../utils';

interface ActivityProps {
  runId: string;
  onBack: () => void;
}

export const Activity: React.FC<ActivityProps> = ({ runId, onBack }) => {
  const [runs, setRuns] = useState<{ run_id: string; status: string }[]>([]);
  const [selected, setSelected] = useState(runId);
  const [evidence, setEvidence] = useState<Record<string, unknown> | null>(null);
  const [status, setStatus] = useState('');

  const loadRuns = async () => {
    try {
      const payload = await listEvidenceRuns();
      setRuns(payload.runs || []);
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  };

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
    <div className="flex flex-col gap-4 pb-24">
      <button onClick={onBack} className="text-xs font-semibold text-primary underline">Back</button>
      <div className="rounded-xl border border-primary/20 bg-white/70 p-4">
        <div className="text-sm font-semibold">Evidence Runs</div>
        <button onClick={loadRuns} className="mt-2 h-9 rounded-lg border border-primary/20 text-sm">Refresh</button>
        <pre className="mt-2 text-[11px] text-text-subtle whitespace-pre-wrap">{JSON.stringify(runs, null, 2)}</pre>
      </div>
      <div className="rounded-xl border border-primary/20 bg-white/70 p-4">
        <div className="text-sm font-semibold">Run ID</div>
        <input className="mt-2 h-9 w-full rounded-lg border border-primary/20 px-3 text-sm" value={selected} onChange={(e) => setSelected(e.target.value)} />
        <div className="mt-2 flex gap-2">
          <button onClick={loadEvidence} className="h-9 flex-1 rounded-lg bg-primary text-background-dark text-sm font-semibold">Fetch Evidence</button>
          <button onClick={downloadZip} className="h-9 flex-1 rounded-lg border border-primary/20 text-sm">Download Export</button>
        </div>
      </div>
      <div className="rounded-xl border border-primary/20 bg-white/70 p-4">
        <div className="text-sm font-semibold">Evidence Bundle</div>
        <pre className="mt-2 text-[11px] text-text-subtle whitespace-pre-wrap">{formatJson(evidence ?? {})}</pre>
      </div>
      {status && <div className="text-xs text-text-subtle">{status}</div>}
    </div>
  );
};
