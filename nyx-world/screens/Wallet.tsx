import React, { useEffect, useState } from 'react';
import { fetchWalletBalance, faucetWallet, transferWallet, PortalSession } from '../api';
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
  const [activeTab, setActiveTab] = useState<'assets' | 'activity'>('assets');
  const [status, setStatus] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const loadBalance = async () => {
    if (!backendOnline || !address.trim()) return;
    setIsLoading(true);
    try {
      const payload = await fetchWalletBalance(address.trim());
      setBalance(payload.balance);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadBalance();
  }, [backendOnline, address]);

  const copyAddress = () => {
    if (!address) return;
    navigator.clipboard.writeText(address);
    setStatus('Address copied!');
    setTimeout(() => setStatus(''), 2000);
  };

  return (
    <div className="flex flex-col h-full text-text-main dark:text-text-main dark:text-white">
      {/* MetaMask Style Account Header */}
      <div className="flex flex-col items-center py-8 bg-gradient-to-b from-primary/10 to-transparent rounded-b-3xl">
        <div className="size-16 rounded-full bg-gradient-to-tr from-primary to-primary-dark shadow-lg mb-4 flex items-center justify-center text-background-dark font-bold text-xl">
          {session?.handle?.[0].toUpperCase() ?? 'N'}
        </div>
        <div className="text-lg font-bold mb-1">@{session?.handle ?? 'User'}</div>
        <button 
          onClick={copyAddress}
          className="flex items-center gap-2 px-3 py-1 rounded-full bg-surface-light dark:bg-surface-dark text-xs text-text-subtle hover:bg-opacity-80 transition-all"
        >
          {address.slice(0, 6)}...{address.slice(-4)}
          <span className="material-symbols-outlined text-sm">content_copy</span>
        </button>
      </div>

      {/* Balance Section */}
      <div className="flex flex-col items-center py-6">
        <div className="text-4xl font-extrabold tracking-tight mb-2">
          {balance !== null ? balance.toLocaleString() : '0'} <span className="text-xl font-normal text-text-subtle">NYXT</span>
        </div>
        <div className="flex gap-4 mt-6">
          <ActionButton icon="add" label="Buy" onClick={() => onNavigate(Screen.FIAT as any)} />
          <ActionButton icon="send" label="Send" onClick={() => {}} />
          <ActionButton icon="swap_horiz" label="Swap" onClick={() => onNavigate(Screen.EXCHANGE)} />
          <ActionButton icon="water_drop" label="Faucet" onClick={() => onNavigate(Screen.FAUCET as any)} />
        </div>
      </div>

      {/* Tabs Section */}
      <div className="flex-1 flex flex-col mt-4">
        <div className="flex border-b border-primary/10">
          <TabButton 
            active={activeTab === 'assets'} 
            onClick={() => setActiveTab('assets')} 
            label="Assets" 
          />
          <TabButton 
            active={activeTab === 'activity'} 
            onClick={() => setActiveTab('activity')} 
            label="Activity" 
          />
        </div>

        <div className="flex-1 overflow-y-auto p-4 no-scrollbar">
          {activeTab === 'assets' ? (
            <div className="flex flex-col gap-4">
              <AssetRow symbol="NYXT" name="NYX Testnet Token" balance={balance ?? 0} />
              <AssetRow symbol="USDX" name="NYX Stablecoin" balance={0} />
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-text-subtle">
              <span className="material-symbols-outlined text-4xl mb-2 opacity-20">history</span>
              <div className="text-sm">No transactions yet</div>
              <button 
                onClick={() => onNavigate(Screen.ACTIVITY)}
                className="mt-2 text-xs text-primary underline"
              >
                View Evidence Center
              </button>
            </div>
          )}
        </div>
      </div>

      {status && (
        <div className="fixed bottom-24 left-1/2 -translate-x-1/2 px-4 py-2 rounded-full bg-background-light dark:bg-background-dark/80 text-text-main dark:text-white text-xs glass">
          {status}
        </div>
      )}
    </div>
  );
};

const ActionButton: React.FC<{ icon: string; label: string; onClick: () => void }> = ({ icon, label, onClick }) => (
  <button 
    onClick={onClick}
    className="flex flex-col items-center gap-2 group"
  >
    <div className="size-12 rounded-full bg-primary flex items-center justify-center text-background-dark shadow-lg group-hover:scale-110 transition-transform">
      <span className="material-symbols-outlined">{icon}</span>
    </div>
    <span className="text-xs font-bold text-primary">{label}</span>
  </button>
);

const TabButton: React.FC<{ active: boolean; onClick: () => void; label: string }> = ({ active, onClick, label }) => (
  <button 
    onClick={onClick}
    className={`flex-1 py-4 text-sm font-bold transition-all border-b-2 ${
      active ? 'text-primary border-primary' : 'text-text-subtle border-transparent'
    }`}
  >
    {label}
  </button>
);

const AssetRow: React.FC<{ symbol: string; name: string; balance: number }> = ({ symbol, name, balance }) => (
  <div className="flex items-center justify-between p-4 rounded-2xl bg-surface-light dark:bg-surface-dark/40 hover:bg-opacity-80 transition-all border border-primary/5">
    <div className="flex items-center gap-3">
      <div className="size-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold">
        {symbol[0]}
      </div>
      <div>
        <div className="font-bold text-sm">{symbol}</div>
        <div className="text-[10px] text-text-subtle uppercase">{name}</div>
      </div>
    </div>
    <div className="text-right">
      <div className="font-bold text-sm">{balance.toLocaleString()}</div>
      <div className="text-[10px] text-text-subtle">≈ $0.00</div>
    </div>
  </div>
);
