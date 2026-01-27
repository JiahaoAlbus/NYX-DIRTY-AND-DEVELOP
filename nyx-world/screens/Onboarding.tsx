import React, { useState } from 'react';
import { createPortalAccount, derivePortalKey, fetchPortalChallenge, verifyPortalChallenge, PortalSession } from '../api';

interface OnboardingProps {
  backendOnline: boolean;
  backendStatus: string;
  onRefresh: () => void;
  onComplete: (session: PortalSession) => void;
}

export const Onboarding: React.FC<OnboardingProps> = ({ backendOnline, backendStatus, onRefresh, onComplete }) => {
  const [handle, setHandle] = useState('');
  const [seed, setSeed] = useState('');
  const [status, setStatus] = useState('');
  const [busy, setBusy] = useState(false);

  const createAccount = async () => {
    if (!backendOnline) {
      setStatus('Backend unavailable');
      return;
    }
    if (!handle.trim()) {
      setStatus('Handle required');
      return;
    }
    if (!seed.trim()) {
      setStatus('Seed required');
      return;
    }
    setBusy(true);
    setStatus('Creating portal account...');
    try {
      const key = derivePortalKey(seed.trim());
      const account = await createPortalAccount(handle.trim(), key.pubkey);
      const challenge = await fetchPortalChallenge(account.account_id);
      const token = await verifyPortalChallenge(account.account_id, challenge.nonce, key.keyBytes);
      onComplete({
        account_id: account.account_id,
        handle: account.handle,
        pubkey: account.pubkey,
        access_token: token.access_token,
      });
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex flex-col gap-6 w-full p-6">
      <div className="text-lg font-semibold text-text-main">NYX Portal Access</div>
      <div className="text-xs text-text-subtle">Testnet Beta. No mainnet claims. No personal data.</div>
      <div className="rounded-lg border border-primary/20 bg-white/80 p-4">
        <div className="text-xs font-semibold text-text-subtle">Backend</div>
        <div className="text-sm font-medium">{backendStatus}</div>
        <button onClick={onRefresh} className="mt-2 text-xs font-semibold text-primary underline">Refresh</button>
      </div>
      <div className="flex flex-col gap-3">
        <label className="flex flex-col gap-1">
          <span className="text-xs font-semibold">Handle</span>
          <input className="h-10 rounded-lg border border-primary/20 px-3" value={handle} onChange={(e) => setHandle(e.target.value)} />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-xs font-semibold">Seed (deterministic)</span>
          <input className="h-10 rounded-lg border border-primary/20 px-3" value={seed} onChange={(e) => setSeed(e.target.value)} />
        </label>
      </div>
      <button
        disabled={busy || !backendOnline}
        onClick={createAccount}
        className="h-11 rounded-xl bg-primary text-background-dark font-semibold"
      >
        {busy ? 'Working...' : 'Create Account + Sign In'}
      </button>
      {status && <div className="text-xs text-text-subtle">{status}</div>}
    </div>
  );
};
