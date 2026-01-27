import React, { useEffect, useMemo, useState } from 'react';
import { Onboarding } from './screens/Onboarding';
import { Home } from './screens/Home';
import { Wallet } from './screens/Wallet';
import { Swap } from './screens/Swap';
import { Chat } from './screens/Chat';
import { Market } from './screens/Market';
import { Activity } from './screens/Activity';
import { BottomNav } from './components/BottomNav';
import { Screen } from './types';
import { checkHealth, fetchCapabilities, PortalSession } from './api';

const SESSION_KEY = 'nyx_portal_session';

const loadSession = (): PortalSession | null => {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as PortalSession;
    if (!parsed || !parsed.access_token) return null;
    return parsed;
  } catch {
    return null;
  }
};

const saveSession = (session: PortalSession | null) => {
  if (!session) {
    localStorage.removeItem(SESSION_KEY);
    return;
  }
  localStorage.setItem(SESSION_KEY, JSON.stringify(session));
};

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Screen>(Screen.HOME);
  const [showActivity, setShowActivity] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);
  const [backendStatus, setBackendStatus] = useState('Backend: unknown');
  const [capabilities, setCapabilities] = useState<Record<string, unknown> | null>(null);
  const [session, setSession] = useState<PortalSession | null>(() => loadSession());
  const [seed, setSeed] = useState('123');
  const [runId, setRunId] = useState('web-run-1');

  useEffect(() => {
    saveSession(session);
  }, [session]);

  const refreshHealth = async () => {
    const ok = await checkHealth();
    setBackendOnline(ok);
    setBackendStatus(ok ? 'Backend: available' : 'Backend: unavailable');
    if (ok) {
      try {
        const caps = await fetchCapabilities();
        setCapabilities(caps);
      } catch {
        setCapabilities(null);
      }
    }
  };

  useEffect(() => {
    refreshHealth();
  }, []);

  const renderScreen = () => {
    if (showActivity) {
      return <Activity runId={runId} onBack={() => setShowActivity(false)} />;
    }
    switch (activeTab) {
      case Screen.HOME:
        return (
          <Home
            backendOnline={backendOnline}
            backendStatus={backendStatus}
            capabilities={capabilities}
            onRefresh={refreshHealth}
            seed={seed}
            runId={runId}
          />
        );
      case Screen.WALLET:
        return (
          <Wallet
            seed={seed}
            runId={runId}
            backendOnline={backendOnline}
            session={session}
            onNavigate={(screen) => {
              if (screen === Screen.ACTIVITY) setShowActivity(true);
              else setActiveTab(screen);
            }}
          />
        );
      case Screen.SWAP:
        return (
          <Swap
            seed={seed}
            runId={runId}
            backendOnline={backendOnline}
          />
        );
      case Screen.CHAT:
        return (
          <Chat
            seed={seed}
            runId={runId}
            backendOnline={backendOnline}
            session={session}
          />
        );
      case Screen.MARKET:
        return (
          <Market
            seed={seed}
            runId={runId}
            backendOnline={backendOnline}
          />
        );
      default:
        return <Home backendOnline={backendOnline} backendStatus={backendStatus} capabilities={capabilities} onRefresh={refreshHealth} />;
    }
  };

  const RunConfig = useMemo(() => {
    return (
      <div className="mt-3 rounded-xl border border-primary/20 bg-white/70 px-4 py-3 text-xs text-text-main shadow-sm">
        <div className="font-semibold uppercase tracking-wider text-text-subtle">Deterministic Run Settings</div>
        <div className="mt-2 grid grid-cols-1 gap-2">
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-medium">Seed (int)</span>
            <input
              className="h-9 rounded-lg border border-primary/20 bg-white px-3 text-sm"
              value={seed}
              onChange={(e) => setSeed(e.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-medium">Run ID</span>
            <input
              className="h-9 rounded-lg border border-primary/20 bg-white px-3 text-sm"
              value={runId}
              onChange={(e) => setRunId(e.target.value)}
            />
          </label>
        </div>
      </div>
    );
  }, [seed, runId]);

  if (!session) {
    return (
      <div className="flex h-screen w-full max-w-md mx-auto shadow-2xl overflow-hidden bg-background-light dark:bg-background-dark">
        <Onboarding
          backendOnline={backendOnline}
          backendStatus={backendStatus}
          onRefresh={refreshHealth}
          onComplete={(next) => setSession(next)}
        />
      </div>
    );
  }

  return (
    <div className="relative flex h-full min-h-screen w-full flex-col max-w-md mx-auto shadow-2xl bg-background-light dark:bg-background-dark overflow-hidden group/design-root">
      <header className="sticky top-0 z-30 flex flex-col gap-2 px-6 pt-safe pb-4 bg-background-light/90 dark:bg-background-dark/90 backdrop-blur-md">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex items-center justify-center size-8 rounded-full bg-primary text-background-dark">
              <span className="material-symbols-outlined text-[20px]">diamond</span>
            </div>
            <div>
              <div className="text-lg font-bold tracking-tight text-text-main dark:text-primary">NYX</div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-text-subtle">Testnet Beta</div>
            </div>
          </div>
          <div className="text-xs font-semibold px-2 py-1 rounded-full border border-primary/20 bg-white/80">
            {backendStatus}
          </div>
        </div>
        {RunConfig}
        {!backendOnline && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
            Backend Offline. Start the gateway at http://127.0.0.1:8091 and tap refresh.
          </div>
        )}
        <button
          className="text-xs font-semibold text-primary underline"
          onClick={() => refreshHealth()}
        >
          Refresh backend status
        </button>
      </header>

      <main className="flex-1 overflow-y-auto no-scrollbar px-6 pb-20 pt-2">
        {renderScreen()}
      </main>

      {!showActivity && <BottomNav activeTab={activeTab} onTabChange={setActiveTab} />}
    </div>
  );
};

export default App;
