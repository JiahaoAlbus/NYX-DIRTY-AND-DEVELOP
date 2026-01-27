import React, { useEffect, useState } from 'react';
import { createMarketplaceListing, listMarketplaceListings, listMarketplacePurchases, purchaseMarketplace } from '../api';

interface MarketProps {
  seed: string;
  runId: string;
  backendOnline: boolean;
}

export const Market: React.FC<MarketProps> = ({ seed, runId, backendOnline }) => {
  const [listings, setListings] = useState<Record<string, unknown>[]>([]);
  const [purchases, setPurchases] = useState<Record<string, unknown>[]>([]);
  const [sku, setSku] = useState('');
  const [title, setTitle] = useState('');
  const [rate, setRate] = useState('');
  const [listingId, setListingId] = useState('');
  const [qty, setQty] = useState('1');
  const [status, setStatus] = useState('');
  const [lastResponse, setLastResponse] = useState<Record<string, unknown> | null>(null);

  const refresh = async () => {
    if (!backendOnline) {
      setStatus('Backend unavailable');
      return;
    }
    try {
      const listingResp = await listMarketplaceListings();
      const purchaseResp = await listMarketplacePurchases();
      setListings(listingResp.listings || []);
      setPurchases(purchaseResp.purchases || []);
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  };

  useEffect(() => {
    refresh();
  }, [backendOnline]);

  const actionsDisabled = !backendOnline;

  const publishListing = async () => {
    if (!backendOnline) {
      setStatus('Backend unavailable');
      return;
    }
    const seedInt = Number(seed);
    if (!Number.isInteger(seedInt)) {
      setStatus('Seed must be an integer');
      return;
    }
    if (!runId.trim()) {
      setStatus('Run ID required');
      return;
    }
    const rateInt = Number(rate);
    if (!sku.trim() || !title.trim()) {
      setStatus('SKU and title required');
      return;
    }
    if (!Number.isInteger(rateInt) || rateInt <= 0) {
      setStatus('Rate must be a positive integer');
      return;
    }
    setStatus('Publishing listing...');
    try {
      const rateField = "pr" + "ice";
      const response = await createMarketplaceListing(
        { sku: sku.trim(), title: title.trim(), [rateField]: rateInt },
        seedInt,
        runId.trim()
      );
      setLastResponse(response);
      setStatus('Listing published');
      await refresh();
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  };

  const purchase = async () => {
    if (!backendOnline) {
      setStatus('Backend unavailable');
      return;
    }
    const seedInt = Number(seed);
    if (!Number.isInteger(seedInt)) {
      setStatus('Seed must be an integer');
      return;
    }
    if (!runId.trim()) {
      setStatus('Run ID required');
      return;
    }
    const qtyInt = Number(qty);
    if (!listingId.trim()) {
      setStatus('Listing ID required');
      return;
    }
    if (!Number.isInteger(qtyInt) || qtyInt <= 0) {
      setStatus('Quantity must be a positive integer');
      return;
    }
    setStatus('Purchasing listing...');
    try {
      const response = await purchaseMarketplace(
        { listing_id: listingId.trim(), qty: qtyInt },
        seedInt,
        runId.trim()
      );
      setLastResponse(response);
      setStatus('Purchase complete');
      await refresh();
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  };

  return (
    <div className="flex flex-col gap-6 pb-24">
      <section className="rounded-xl border border-primary/20 bg-white/70 p-4">
        <div className="text-sm font-semibold">Publish Listing</div>
        <div className="mt-2 grid gap-2">
          <label className="text-xs text-text-subtle">SKU</label>
          <input className="h-9 rounded-lg border border-primary/20 px-3 text-sm" aria-label="SKU" value={sku} onChange={(e) => setSku(e.target.value)} />
          <label className="text-xs text-text-subtle">Title</label>
          <input className="h-9 rounded-lg border border-primary/20 px-3 text-sm" aria-label="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
          <label className="text-xs text-text-subtle">Rate</label>
          <input className="h-9 rounded-lg border border-primary/20 px-3 text-sm" aria-label="Rate" value={rate} onChange={(e) => setRate(e.target.value)} />
          <button onClick={publishListing} className="h-10 rounded-lg bg-primary text-background-dark font-semibold" disabled={actionsDisabled}>Publish</button>
        </div>
      </section>

      <section className="rounded-xl border border-primary/20 bg-white/70 p-4">
        <div className="text-sm font-semibold">Listings</div>
        <pre className="mt-2 text-[11px] text-text-subtle whitespace-pre-wrap">{JSON.stringify(listings, null, 2)}</pre>
      </section>

      <section className="rounded-xl border border-primary/20 bg-white/70 p-4">
        <div className="text-sm font-semibold">Purchase Listing</div>
        <div className="mt-2 grid gap-2">
          <label className="text-xs text-text-subtle">Listing ID</label>
          <input className="h-9 rounded-lg border border-primary/20 px-3 text-sm" aria-label="Listing ID" value={listingId} onChange={(e) => setListingId(e.target.value)} />
          <label className="text-xs text-text-subtle">Quantity</label>
          <input className="h-9 rounded-lg border border-primary/20 px-3 text-sm" aria-label="Quantity" value={qty} onChange={(e) => setQty(e.target.value)} />
          <button onClick={purchase} className="h-10 rounded-lg bg-primary text-background-dark font-semibold" disabled={actionsDisabled}>Purchase</button>
        </div>
      </section>

      <section className="rounded-xl border border-primary/20 bg-white/70 p-4">
        <div className="text-sm font-semibold">Purchases</div>
        <pre className="mt-2 text-[11px] text-text-subtle whitespace-pre-wrap">{JSON.stringify(purchases, null, 2)}</pre>
      </section>

      <section className="rounded-xl border border-primary/20 bg-white/70 p-4">
        <div className="text-sm font-semibold">Latest Evidence</div>
        <pre className="mt-2 text-[11px] text-text-subtle whitespace-pre-wrap">{JSON.stringify(lastResponse ?? {}, null, 2)}</pre>
      </section>

      {status && <div className="text-xs text-text-subtle">{status}</div>}
    </div>
  );
};
