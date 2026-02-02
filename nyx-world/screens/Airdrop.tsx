import React, { useState } from 'react';
import { Gift, CheckCircle2, Circle, Trophy } from 'lucide-react';
import { claimAirdrop, PortalSession } from '../api';

interface AirdropProps {
  seed: string;
  runId: string;
  backendOnline: boolean;
  session: PortalSession | null;
}

export const Airdrop: React.FC<AirdropProps> = ({ seed, runId, backendOnline, session }) => {
  const [claimed, setClaimed] = useState<string[]>([]);
  const [status, setStatus] = useState('');

  const tasks = [
    { id: 't1', title: 'Follow NYX on X', reward: 50000000 },
    { id: 't2', title: 'Join Discord Community', reward: 50000000 },
    { id: 't3', title: 'First Trade on Exchange', reward: 100000000 },
    { id: 't4', title: 'Buy an item in Store', reward: 100000000 },
  ];

  const handleClaim = async (id: string, reward: number) => {
    if (claimed.includes(id) || !backendOnline || !session) return;
    setStatus('Claiming reward...');
    try {
      await claimAirdrop(session.access_token, session.account_id, id, reward);
      setClaimed([...claimed, id]);
      setStatus('Reward claimed successfully!');
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  };

  return (
    <div className="flex flex-col gap-6 text-text-main dark:text-white pb-24">
      <div className="p-8 rounded-3xl bg-gradient-to-br from-primary/20 to-purple-600/20 glass border border-white/10 flex flex-col items-center text-center">
        <div className="size-20 rounded-full bg-primary flex items-center justify-center text-black mb-4 shadow-2xl">
          <Trophy size={40} />
        </div>
        <h2 className="text-2xl font-bold">NYX Ecosystem Airdrop</h2>
        <p className="text-sm text-text-subtle mt-2">Complete tasks to earn testnet rewards</p>
      </div>

      <div className="flex flex-col gap-4">
        <h3 className="font-bold px-2 flex items-center gap-2"><Gift size={18} className="text-primary" /> Available Tasks</h3>
        {tasks.map(task => (
          <div key={task.id} className="p-5 rounded-3xl glass bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5 flex items-center justify-between group">
            <div className="flex items-center gap-4">
              <div className={`size-10 rounded-xl flex items-center justify-center ${claimed.includes(task.id) ? 'bg-binance-green/20 text-binance-green' : 'bg-primary/20 text-primary'}`}>
                {claimed.includes(task.id) ? <CheckCircle2 size={24} /> : <Circle size={24} />}
              </div>
              <div>
                <div className="font-bold text-sm">{task.title}</div>
                <div className="text-xs text-primary">+{task.reward} NYXT</div>
              </div>
            </div>
            <button 
              onClick={() => handleClaim(task.id, task.reward)}
              disabled={claimed.includes(task.id)}
              className={`px-6 py-2 rounded-xl text-xs font-bold transition-all ${
                claimed.includes(task.id) ? 'bg-surface-light dark:bg-surface-dark text-text-subtle' : 'bg-primary text-black hover:scale-105 active:scale-95'
              }`}
            >
              {claimed.includes(task.id) ? 'Claimed' : 'Claim'}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
