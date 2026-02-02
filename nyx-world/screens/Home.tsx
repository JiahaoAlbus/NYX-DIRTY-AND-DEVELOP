import React, { useEffect, useState } from 'react';
import { Screen } from '../types';
import { fetchDiscoveryFeed } from '../api';
import { 
  Zap, 
  Droplets, 
  ArrowLeftRight, 
  ShieldCheck, 
  LayoutGrid, 
  ShoppingBag, 
  MessageCircle, 
  Wallet as WalletIcon,
  Globe,
  Gift
} from 'lucide-react';

interface HomeProps {
  backendOnline: boolean;
  backendStatus: string;
  capabilities: Record<string, unknown> | null;
  onRefresh: () => void;
  seed: string;
  runId: string;
  onNavigate: (screen: Screen) => void;
}

export const Home: React.FC<HomeProps> = ({ 
  backendOnline, 
  onRefresh, 
  onNavigate,
  capabilities
}) => {
  const [feed, setFeed] = useState<any[]>([]);

  useEffect(() => {
    const loadFeed = async () => {
      if (!backendOnline) return;
      try {
        const data = await fetchDiscoveryFeed();
        setFeed(data.feed || []);
      } catch (err) {
        console.error('Failed to load feed:', err);
      }
    };
    loadFeed();
  }, [backendOnline]);

  const isModuleEnabled = (module: string, feature: string) => {
    if (!capabilities) return true; // default to true if capabilities not yet loaded
    const mod = capabilities.modules?.[module];
    return mod?.[feature] !== 'disabled';
  };

  return (
    <div className="flex flex-col gap-6 pb-24">
      {/* IG Stories Bar */}
      <div className="px-6 -mx-6 overflow-x-auto no-scrollbar flex gap-4 py-2">
        <div className="flex-shrink-0 flex flex-col items-center gap-1 pl-6">
          <div className="size-16 rounded-full p-1 border-2 border-dashed border-primary/40 flex items-center justify-center">
            <div className="size-full rounded-full bg-surface-light dark:bg-surface-dark flex items-center justify-center relative">
              <span className="material-symbols-outlined text-primary">add</span>
              <div className="absolute -bottom-1 -right-1 size-5 bg-primary rounded-full border-2 border-white dark:border-background-dark flex items-center justify-center">
                <span className="text-black font-bold text-[10px]">+</span>
              </div>
            </div>
          </div>
          <span className="text-[10px] text-text-subtle">Your Story</span>
        </div>
        {[1,2,3,4,5].map(i => (
          <div key={i} className="flex-shrink-0 flex flex-col items-center gap-1">
            <div className="size-16 rounded-full p-1 bg-gradient-to-tr from-[#f9ce34] via-[#ee2a7b] to-[#6228d7]">
              <div className="size-full rounded-full border-2 border-white dark:border-background-dark overflow-hidden bg-surface-light">
                <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=story-${i}`} alt="avatar" />
              </div>
            </div>
            <span className="text-[10px] text-text-subtle">user_{i}</span>
          </div>
        ))}
      </div>

      {/* Wallet Glance */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-primary to-primary-dark p-6 shadow-2xl glass">
        <div className="relative z-10 flex flex-col gap-2">
          <h2 className="text-2xl font-black text-black leading-tight">Secure Your Future with NYX</h2>
          <p className="text-xs font-bold text-black/60 uppercase tracking-widest">Deterministic Web3 Ecosystem</p>
          <button 
            onClick={() => onNavigate(Screen.AIRDROP)}
            className="mt-4 w-fit rounded-xl bg-black px-6 py-2.5 text-xs font-bold text-primary shadow-xl hover:scale-105 active:scale-95 transition-all"
          >
            Claim Airdrop
          </button>
        </div>
        <div className="absolute -right-8 -top-8 size-48 rounded-full bg-black/5 blur-3xl" />
        <div className="absolute right-4 bottom-4 opacity-20 text-black">
          <Zap size={80} strokeWidth={3} />
        </div>
      </div>

      {/* Quick Actions Grid (Binance Style) */}
      <div className="grid grid-cols-4 gap-4">
        <Shortcut icon={<Droplets size={20} />} label="Faucet" onClick={() => onNavigate(Screen.FAUCET)} />
        <Shortcut icon={<ArrowLeftRight size={20} />} label="Fiat" onClick={() => onNavigate(Screen.FIAT)} />
        <Shortcut icon={<Gift size={20} />} label="Airdrop" onClick={() => onNavigate(Screen.AIRDROP)} />
        <Shortcut icon={<LayoutGrid size={20} />} label="More" onClick={() => {}} />
      </div>
      
      {/* Ecosystem Modules */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between px-2">
          <h3 className="text-sm font-bold uppercase tracking-widest text-text-subtle">Core Modules</h3>
          <button onClick={onRefresh} className="text-[10px] text-primary font-bold">Refresh Status</button>
        </div>
        
        <div className="grid grid-cols-1 gap-3">
          <ModuleCard 
            icon={<WalletIcon className="text-primary" />} 
            title="Web3 Wallet" 
            desc="Secure MetaMask-style asset management"
            onClick={() => onNavigate(Screen.WALLET)}
          />
          <ModuleCard 
            icon={<ArrowLeftRight className="text-binance-green" />} 
            title="Exchange" 
            desc="Pro-grade trading with deep liquidity"
            onClick={() => onNavigate(Screen.EXCHANGE)}
          />
          <ModuleCard 
            icon={<MessageCircle className="text-blue-400" />} 
            title="Chat" 
            desc="Instagram-style P2P encrypted social"
            onClick={() => onNavigate(Screen.CHAT)}
          />
          <ModuleCard 
            icon={<ShoppingBag className="text-orange-400" />} 
            title="Store" 
            desc="Deterministic marketplace for dApps"
            onClick={() => onNavigate(Screen.STORE)}
          />
          {isModuleEnabled('dapp', 'browser') && (
            <ModuleCard 
              icon={<Globe className="text-purple-400" />} 
              title="Web2 Guard" 
              desc="Encrypted access to external APIs"
              onClick={() => onNavigate(Screen.WEB2_ACCESS)}
            />
          )}
        </div>
      </div>

      {/* Discovery Feed: IG Style */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between px-2">
          <h3 className="font-black text-lg tracking-tight">Explore NYX</h3>
          <button className="text-xs font-bold text-primary">View All</button>
        </div>
        
        <div className="grid grid-cols-2 gap-3">
          {feed.length === 0 ? (
            <>
              <div className="aspect-square rounded-2xl bg-surface-light dark:bg-surface-dark overflow-hidden relative group cursor-pointer">
                <img 
                  src="https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=400&q=80" 
                  className="size-full object-cover group-hover:scale-110 transition-transform duration-500"
                  alt="nft"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex flex-col justify-end p-3">
                  <span className="text-[10px] font-bold text-primary">NEW LISTING</span>
                  <span className="text-xs font-bold text-white truncate">Cyber Artifact #42</span>
                </div>
              </div>
              <div className="aspect-square rounded-2xl bg-surface-light dark:bg-surface-dark overflow-hidden relative group cursor-pointer">
                <img 
                  src="https://images.unsplash.com/photo-1620641788421-7a1c342ea42e?w=400&q=80" 
                  className="size-full object-cover group-hover:scale-110 transition-transform duration-500"
                  alt="nft"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex flex-col justify-end p-3">
                  <span className="text-[10px] font-bold text-binance-green">ACTIVE ROOM</span>
                  <span className="text-xs font-bold text-white truncate">Dev Lounge</span>
                </div>
              </div>
            </>
          ) : (
            feed.map((item, i) => (
              <div key={i} className="aspect-square rounded-2xl bg-surface-light dark:bg-surface-dark overflow-hidden relative group cursor-pointer">
                <img 
                  src={`https://api.dicebear.com/7.x/initials/svg?seed=${item.data.name || item.data.title}`} 
                  className="size-full object-cover group-hover:scale-110 transition-transform duration-500"
                  alt="feed-item"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex flex-col justify-end p-3">
                  <span className="text-[10px] font-bold text-primary">{item.type.toUpperCase()}</span>
                  <span className="text-xs font-bold text-white truncate">{item.data.name || item.data.title}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

const Shortcut: React.FC<{ icon: React.ReactNode; label: string; onClick: () => void }> = ({ icon, label, onClick }) => (
  <button 
    onClick={onClick}
    className="flex flex-col items-center gap-2 group"
  >
    <div className="size-12 rounded-2xl bg-surface-light dark:bg-surface-dark/40 flex items-center justify-center text-primary border border-black/5 dark:border-white/5 group-hover:bg-primary group-hover:text-black transition-all shadow-lg">
      {icon}
    </div>
    <span className="text-[10px] font-bold text-text-subtle group-hover:text-text-main dark:text-white">{label}</span>
  </button>
);

const ModuleCard: React.FC<{ icon: React.ReactNode; title: string; desc: string; onClick: () => void }> = ({ icon, title, desc, onClick }) => (
  <button 
    onClick={onClick}
    className="flex items-center gap-4 p-4 rounded-3xl glass bg-surface-light dark:bg-surface-dark/20 border border-black/5 dark:border-white/5 hover:bg-surface-light/80 dark:hover:bg-surface-dark/40 transition-all text-left group"
  >
    <div className="size-12 rounded-2xl bg-surface-light dark:bg-surface-dark flex items-center justify-center shadow-inner group-hover:scale-110 transition-transform">
      {icon}
    </div>
    <div className="flex-1">
      <div className="text-sm font-bold">{title}</div>
      <div className="text-[10px] text-text-subtle line-clamp-1">{desc}</div>
    </div>
    <span className="material-symbols-outlined text-text-subtle opacity-0 group-hover:opacity-100 transition-all">chevron_right</span>
  </button>
);
