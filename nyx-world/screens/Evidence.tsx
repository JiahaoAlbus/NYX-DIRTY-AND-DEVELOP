import React, { useEffect, useState } from "react";
import { fetchEvidence, listEvidenceRuns, EvidenceBundle } from "../api";

export const Evidence: React.FC = () => {
  const [runs, setRuns] = useState<{ run_id: string; status: string }[]>([]);
  const [selectedRun, setSelectedRun] = useState<string | null>(null);
  const [bundle, setBundle] = useState<EvidenceBundle | null>(null);

  const refresh = async () => {
    try {
      const data = await listEvidenceRuns();
      setRuns(data.runs);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  useEffect(() => {
    if (selectedRun) {
      fetchEvidence(selectedRun).then(setBundle).catch(console.error);
    }
  }, [selectedRun]);

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-xl font-bold">Evidence Center</h2>
      <div className="flex flex-col gap-2">
        {runs.map((run) => (
          <button
            key={run.run_id}
            onClick={() => setSelectedRun(run.run_id)}
            className={`p-3 rounded-lg border ${selectedRun === run.run_id ? "border-primary bg-primary/10" : "border-primary/20 bg-white"}`}
          >
            <div className="text-sm font-bold">{run.run_id}</div>
            <div className="text-xs text-text-subtle">{run.status}</div>
          </button>
        ))}
      </div>
      {bundle && (
        <div className="p-4 rounded-xl bg-white border border-primary/20 shadow-sm overflow-hidden">
          <h3 className="font-bold mb-2">Run Details</h3>
          <div className="text-xs space-y-2">
            <div>
              <span className="font-bold">Protocol Anchor:</span> {bundle.protocol_anchor}
            </div>
            <div>
              <span className="font-bold">Replay OK:</span> {bundle.replay_ok ? "✅" : "❌"}
            </div>
            <div className="mt-2">
              <div className="font-bold">Receipt Hashes:</div>
              <ul className="list-disc list-inside">
                {bundle.receipt_hashes.map((h, i) => (
                  <li key={i} className="truncate">
                    {h}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
