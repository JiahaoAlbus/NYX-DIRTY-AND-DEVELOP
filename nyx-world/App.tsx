import React, { useEffect, useMemo, useState } from 'react';
import { Onboarding } from './screens/Onboarding';
import { Airdrop } from './screens/Airdrop';
import { Faucet } from './screens/Faucet';
import { Fiat } from './screens/Fiat';
import { Web2Access } from './screens/Web2Access';
import { Home } from './screens/Home';
import { Wallet } from './screens/Wallet';
import { Exchange } from './screens/Exchange';
import { Chat } from './screens/Chat';
import { Store } from './screens/Store';
import { Activity } from './screens/Activity';
import { Settings } from './screens/Settings';
import { DappBrowser } from './screens/DappBrowser';
import { BottomNav } from './components/BottomNav';
import { Screen } from './types';
import { checkHealth, fetchCapabilities, PortalSession } from './api';

const SESSION_KEY = 'nyx_portal_session';

const loadSession = (): PortalSession | null => {
  // Check for injected session token from iOS
  const injectedToken = (window as any).__NYX_SESSION_TOKEN__;
  if (injectedToken) {
    return { 
      access_token: injectedToken, 
      account_id: "injected",
      handle: "Injected User",
      pubkey: ""
    }; 
  }

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

const getInitialTab = (): Screen => {
  const injectedScreen = (window as any).__NYX_INITIAL_SCREEN__;
  if (injectedScreen === 'exchange') return Screen.EXCHANGE;
  if (injectedScreen === 'chat') return Screen.CHAT;
  if (injectedScreen === 'store') return Screen.STORE;
  return Screen.HOME;
};

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Screen>(() => getInitialTab());
  const [backendOnline, setBackendOnline] = useState(false);
  const [backendStatus, setBackendStatus] = useState('Backend: unknown');
  const [capabilities, setCapabilities] = useState<Record<string, unknown> | null>(null);
  const [session, setSession] = useState<PortalSession | null>(() => loadSession());
  const [seed, setSeed] = useState('123');
  const [runId, setRunId] = useState('web-run-1');
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem('nyx_theme');
    return saved ? saved === 'dark' : true; // Default to dark
  });

  useEffect(() => {
    localStorage.setItem('nyx_theme', isDark ? 'dark' : 'light');
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDark]);

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
            onNavigate={setActiveTab}
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
              setActiveTab(screen);
            }}
          />
        );
      case Screen.EXCHANGE:
        return (
          <Exchange
            seed={seed}
            runId={runId}
            backendOnline={backendOnline}
            session={session}
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
      case Screen.STORE:
        return (
          <Store
            seed={seed}
            runId={runId}
            backendOnline={backendOnline}
            session={session}
          />
        );
      case Screen.ACTIVITY:
        return <Activity runId={runId} onBack={() => setActiveTab(Screen.HOME)} session={session} />;
      case Screen.EVIDENCE:
        return <Activity runId={runId} onBack={() => setActiveTab(Screen.HOME)} session={session} />;
      case Screen.SETTINGS:
        return (
          <Settings 
            session={session}
            seed={seed}
            runId={runId}
            onSeedChange={setSeed}
            onRunIdChange={setRunId}
            onLogout={() => setSession(null)}
          />
        );
      case Screen.DAPP_BROWSER:
        return <DappBrowser />;
      case Screen.AIRDROP:
        return (
          <Airdrop
            seed={seed}
            runId={runId}
            backendOnline={backendOnline}
            session={session}
          />
        );
      case Screen.FAUCET:
        return <Faucet seed={seed} runId={runId} backendOnline={backendOnline} session={session} />;
      case Screen.FIAT:
        return <Fiat />;
      case Screen.WEB2_ACCESS:
        return <Web2Access />;
      default:
        return <Home 
          backendOnline={backendOnline} 
          backendStatus={backendStatus} 
          capabilities={capabilities} 
          onRefresh={refreshHealth} 
          seed={seed} 
          runId={runId}
          onNavigate={setActiveTab}
        />;
    }
  };



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
    <div className="relative flex h-full min-h-screen w-full flex-col max-w-md mx-auto shadow-2xl bg-background-light dark:bg-background-dark text-text-main dark:text-white overflow-hidden group/design-root">
      <header className="sticky top-0 z-30 flex flex-col gap-2 px-6 pt-safe pb-4 bg-background-light/70 dark:bg-background-dark/70 backdrop-blur-xl border-b border-primary/10">
        <div className="flex items-center justify-between mt-2">
          <div className="flex items-center gap-2">
            <div className="flex items-center justify-center size-8 rounded-full bg-primary text-background-dark shadow-lg">
              <span className="material-symbols-outlined text-[20px] font-bold">diamond</span>
            </div>
            <div>
              <div className="text-lg font-bold tracking-tight text-text-main dark:text-primary leading-none">NYX</div>
              <div className="text-[10px] font-extrabold uppercase tracking-widest text-text-subtle">Ecosystem</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button 
              onClick={() => setIsDark(!isDark)}
              className="size-8 rounded-full bg-surface-light dark:bg-surface-dark flex items-center justify-center text-text-subtle hover:text-primary transition-all"
            >
              <span className="material-symbols-outlined text-[18px]">
                {isDark ? 'light_mode' : 'dark_mode'}
              </span>
            </button>
            <div className={`text-[10px] font-bold px-3 py-1 rounded-full border ${backendOnline ? 'border-binance-green/30 bg-binance-green/10 text-binance-green' : 'border-binance-red/30 bg-binance-red/10 text-binance-red'}`}>
              {backendOnline ? 'ONLINE' : 'OFFLINE'}
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto no-scrollbar px-6 pb-20 pt-4">
        {renderScreen()}
      </main>

      <BottomNav activeTab={activeTab} onTabChange={setActiveTab} />
    </div>
  );
};

export default App;
