import React, { useEffect, useState } from 'react';
import { PortalSession, publishListing, listMarketplaceListings, listMarketplacePurchases, purchaseMarketplace } from '../api';
import { ShoppingCart, Search, Filter, Tag, Package, ChevronRight } from 'lucide-react';

interface MarketProps {
  seed: string;
  runId: string;
  backendOnline: boolean;
  session: PortalSession | null;
}

export const Store: React.FC<MarketProps> = ({ seed, runId, backendOnline, session }) => {
  const [listings, setListings] = useState<any[]>([]);
  const [purchases, setPurchases] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeCategory, setCategory] = useState('All');
  const [status, setStatus] = useState('');

  const refresh = async () => {
    if (!backendOnline) return;
    try {
      const listingResp = await listMarketplaceListings();
      const purchaseResp = await listMarketplacePurchases();
      setListings(listingResp.listings || []);
      setPurchases(purchaseResp.purchases || []);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    refresh();
  }, [backendOnline]);

  const handlePurchase = async (listingId: string) => {
    if (!backendOnline || !session) return;
    setStatus('Processing payment...');
    try {
      await purchaseMarketplace(session.access_token, session.account_id, listingId, 1);
      setStatus('Purchase successful! Evidence recorded.');
      refresh();
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  };

  const categories = ['All', 'NFTs', 'Virtual Land', 'In-game Items', 'DeFi Tools'];

  return (
    <div className="flex flex-col gap-6 pb-24 text-text-main dark:text-text-main dark:text-white">
      {/* Header & Search */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-4">
          <div className="flex-1 flex items-center gap-2 px-4 py-2 bg-surface-light dark:bg-surface-dark rounded-2xl border border-primary/10 glass">
            <Search size={18} className="text-text-subtle" />
            <input 
              className="flex-1 bg-transparent outline-none text-sm"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <button className="size-10 rounded-2xl bg-primary flex items-center justify-center text-black shadow-lg">
            <ShoppingCart size={20} />
          </button>
        </div>

        {/* Categories */}
        <div className="flex gap-2 overflow-x-auto no-scrollbar pb-2">
          {categories.map(cat => (
            <button 
              key={cat}
              onClick={() => setCategory(cat)}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all whitespace-nowrap ${
                activeCategory === cat ? 'bg-primary text-black' : 'bg-surface-light dark:bg-surface-dark text-text-subtle'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-2 gap-4">
        {listings.map((item, i) => (
          <div key={i} className="flex flex-col rounded-3xl overflow-hidden glass bg-white dark:bg-surface-light dark:bg-surface-dark/40 border border-primary/5 shadow-xl hover:translate-y-[-4px] transition-all group">
            <div className="aspect-square bg-gradient-to-br from-primary/20 to-primary-dark/40 relative overflow-hidden">
              <div className="absolute inset-0 flex items-center justify-center text-primary/40 group-hover:scale-110 transition-transform">
                <Package size={64} />
              </div>
              <div className="absolute top-3 left-3 px-2 py-1 rounded-lg bg-black/50 backdrop-blur-md text-[10px] font-bold text-primary">
                NEW
              </div>
            </div>
            <div className="p-4 flex flex-col gap-2">
              <div className="text-xs text-text-subtle font-medium uppercase tracking-wider">{item.sku}</div>
              <div className="font-bold text-sm line-clamp-2 min-h-[40px]">{item.title}</div>
              <div className="flex items-center justify-between mt-2">
                <div className="flex flex-col">
                  <span className="text-[10px] text-text-subtle">Rate</span>
                  <span className="text-primary font-extrabold text-lg">{item.rate} <span className="text-xs">NYXT</span></span>
                </div>
                <button 
                  onClick={() => handlePurchase(item.listing_id)}
                  className="size-10 rounded-xl bg-primary text-black flex items-center justify-center hover:scale-105 active:scale-95 transition-all shadow-lg"
                >
                  <ShoppingCart size={18} />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Purchases */}
      {purchases.length > 0 && (
        <div className="mt-8 flex flex-col gap-4">
          <div className="flex items-center justify-between px-2">
            <h3 className="font-bold flex items-center gap-2"><Tag size={18} className="text-primary" /> Recent Orders</h3>
            <button className="text-xs text-primary font-bold flex items-center">View All <ChevronRight size={14} /></button>
          </div>
          <div className="flex flex-col gap-3">
            {purchases.slice(0, 3).map((p, i) => (
              <div key={i} className="flex items-center gap-4 p-4 rounded-3xl glass bg-surface-light dark:bg-surface-dark/20 border border-primary/5">
                <div className="size-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary">
                  <Package size={24} />
                </div>
                <div className="flex-1">
                  <div className="text-sm font-bold truncate">Order #{p.purchase_id.slice(0, 8)}</div>
                  <div className="text-[10px] text-text-subtle">Qty: {p.qty} ● {new Date(p.created_at).toLocaleDateString()}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold text-primary">Success</div>
                  <div className="text-[10px] text-text-subtle">Evidence OK</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {status && (
        <div className="fixed bottom-24 left-1/2 -translate-x-1/2 px-6 py-3 rounded-2xl bg-primary text-black text-sm font-bold shadow-2xl glass-dark animate-in zoom-in">
          {status}
        </div>
      )}
    </div>
  );
};
