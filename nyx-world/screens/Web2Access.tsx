import React, { useState } from 'react';
import { Shield, Globe, Lock, Key, Eye, EyeOff, AlertTriangle } from 'lucide-react';

export const Web2Access: React.FC = () => {
  const [url, setUrl] = useState('https://api.github.com/user');
  const [apiKey, setApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);

  return (
    <div className="flex flex-col gap-6 text-text-main dark:text-white pb-24">
      <div className="p-8 rounded-3xl bg-gradient-to-br from-blue-600/20 to-purple-600/20 glass border border-white/10 flex flex-col items-center text-center">
        <div className="size-20 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-500 mb-4 shadow-2xl border border-blue-500/30">
          <Globe size={40} />
        </div>
        <h2 className="text-2xl font-bold">Web2 Encrypted Access</h2>
        <p className="text-sm text-text-subtle mt-2">Mediate your Web2 data through NYX Privacy Guard</p>
      </div>

      <div className="flex flex-col gap-4">
        <div className="p-6 rounded-3xl glass bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5 flex flex-col gap-6">
          <div className="flex flex-col gap-2">
            <label className="text-[10px] text-text-subtle uppercase px-1">Target Endpoint</label>
            <div className="flex items-center gap-3 px-4 py-3 bg-background-light dark:bg-background-dark rounded-2xl border border-black/5 dark:border-white/5">
              <Globe size={18} className="text-text-subtle" />
              <input 
                className="bg-transparent flex-1 outline-none text-sm font-mono"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-[10px] text-text-subtle uppercase px-1">Authorization Key (Encrypted Locally)</label>
            <div className="flex items-center gap-3 px-4 py-3 bg-background-light dark:bg-background-dark rounded-2xl border border-black/5 dark:border-white/5">
              <Key size={18} className="text-text-subtle" />
              <input 
                type={showKey ? 'text' : 'password'}
                className="bg-transparent flex-1 outline-none text-sm font-mono"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
              />
              <button onClick={() => setShowKey(!showKey)} className="text-text-subtle hover:text-text-main dark:text-white transition-colors">
                {showKey ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-orange-500/5 border border-orange-500/10 flex gap-3 items-start">
            <AlertTriangle size={16} className="text-orange-500 shrink-0 mt-0.5" />
            <div className="text-[10px] text-text-subtle leading-relaxed">
              Your key will be encrypted on-device before being sent through the NYX mediation layer. 
              Only the target endpoint can decrypt and use it for the session.
            </div>
          </div>

          <button 
            onClick={() => setIsConnecting(true)}
            className="w-full py-4 rounded-2xl bg-blue-500 text-text-main dark:text-white font-bold flex items-center justify-center gap-2 hover:bg-blue-600 transition-all shadow-xl"
          >
            {isConnecting ? 'Connecting Guard...' : 'Establish Secure Connection'}
          </button>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-3xl glass bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5 flex flex-col items-center gap-2 text-center">
            <Shield size={24} className="text-blue-500" />
            <div className="text-[10px] font-bold">Identity Obfuscation</div>
          </div>
          <div className="p-4 rounded-3xl glass bg-surface-light dark:bg-surface-dark/40 border border-black/5 dark:border-white/5 flex flex-col items-center gap-2 text-center">
            <Lock size={24} className="text-purple-500" />
            <div className="text-[10px] font-bold">Metadata Privacy</div>
          </div>
        </div>
      </div>
    </div>
  );
};
