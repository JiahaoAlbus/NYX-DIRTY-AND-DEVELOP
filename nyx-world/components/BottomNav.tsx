import React from 'react';
import { Screen } from '../types';

interface BottomNavProps {
  activeTab: Screen;
  onTabChange: (tab: Screen) => void;
}

export const BottomNav: React.FC<BottomNavProps> = ({ activeTab, onTabChange }) => {
  const getButtonClass = (isActive: boolean) => 
    `flex flex-1 flex-col items-center gap-1 p-2 group transition-colors duration-300 ${isActive ? 'text-text-main dark:text-white' : 'text-text-subtle dark:text-gray-400 hover:text-text-main dark:hover:text-primary'}`;

  return (
    <nav className="fixed bottom-0 z-40 w-full max-w-md mx-auto bg-white/90 dark:bg-[#1f1c13]/90 backdrop-blur-xl border-t border-primary/10 pb-safe">
      <div className="flex items-center justify-between px-2 pt-2 pb-2">
        {/* World (Home) */}
        <button className={getButtonClass(activeTab === Screen.HOME)} onClick={() => onTabChange(Screen.HOME)}>
          <div className="relative">
            <span className={`material-symbols-outlined text-[26px] ${activeTab === Screen.HOME ? 'filled text-primary' : ''}`}>public</span>
            {activeTab === Screen.HOME && <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-primary"></span>}
          </div>
          <span className="text-[10px] font-medium">World</span>
        </button>

        {/* Wallet */}
        <button className={getButtonClass(activeTab === Screen.WALLET)} onClick={() => onTabChange(Screen.WALLET)}>
          <span className={`material-symbols-outlined text-[26px] group-hover:scale-105 transition-transform ${activeTab === Screen.WALLET ? 'filled text-primary' : ''}`}>account_balance_wallet</span>
          <span className="text-[10px] font-medium">Wallet</span>
        </button>

        {/* Swap (Center Highlighted) */}
        <button className="flex flex-1 flex-col items-center gap-1 p-2 group" onClick={() => onTabChange(Screen.SWAP)}>
          <div className={`p-2 rounded-xl -mt-6 mb-1 shadow-lg border border-primary/20 transition-all duration-300 ${activeTab === Screen.SWAP ? 'bg-primary text-black' : 'bg-primary/10 dark:bg-primary/20 text-primary'}`}>
            <span className="material-symbols-outlined text-[28px] group-hover:rotate-180 transition-transform duration-500">currency_exchange</span>
          </div>
          <span className={`text-[10px] font-medium translate-y-[-4px] ${activeTab === Screen.SWAP ? 'text-primary' : 'text-text-subtle dark:text-gray-400'}`}>Swap</span>
        </button>

        {/* Chat */}
        <button className={getButtonClass(activeTab === Screen.CHAT)} onClick={() => onTabChange(Screen.CHAT)}>
          <span className={`material-symbols-outlined text-[26px] group-hover:scale-105 transition-transform ${activeTab === Screen.CHAT ? 'filled text-primary' : ''}`}>chat_bubble</span>
          <span className="text-[10px] font-medium">Chat</span>
        </button>

        {/* Market */}
        <button className={getButtonClass(activeTab === Screen.MARKET)} onClick={() => onTabChange(Screen.MARKET)}>
          <span className={`material-symbols-outlined text-[26px] group-hover:scale-105 transition-transform ${activeTab === Screen.MARKET ? 'filled text-primary' : ''}`}>storefront</span>
          <span className="text-[10px] font-medium">Market</span>
        </button>
      </div>
    </nav>
  );
};