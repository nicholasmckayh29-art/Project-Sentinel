"use client";

import { createClient } from "@/lib/supabase/client";
import Link from "next/link";
import { useState } from "react";

export default function PricingPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function checkout() {
    setLoading(true);
    setError(null);
    const supabase = createClient();
    const { data: { user } } = await supabase.auth.getUser();

    if (!user) {
      window.location.href = "/login";
      return;
    }

    const res = await fetch("/api/stripe/checkout", { method: "POST" });
    const data = await res.json();
    setLoading(false);

    if (!res.ok) {
      setError(data.error ?? "Checkout failed");
      return;
    }
    if (data.url) window.location.href = data.url;
  }

  return (
    <main className="flex-1 px-4 py-12 max-w-2xl mx-auto w-full space-y-8">
      <div>
        <p className="badge-classified inline-block mb-2">ACCESS REQUEST</p>
        <h1 className="font-mono text-3xl text-accent terminal-glow">CLEARANCE LEVELS</h1>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="card-terminal p-6 space-y-4">
          <h2 className="font-mono text-accent">LEVEL 1 — FREE</h2>
          <ul className="font-mono text-xs space-y-2 text-muted">
            <li>◉ Model catalog browse</li>
            <li>◉ 3 watchlist items</li>
            <li>◉ Alerts delayed 24h</li>
            <li>◉ 7-day price history</li>
          </ul>
          <Link href="/login" className="font-mono text-xs border border-border px-4 py-2 inline-block">
            SIGN IN FREE
          </Link>
        </div>

        <div className="card-terminal p-6 space-y-4 border-accent">
          <h2 className="font-mono text-accent terminal-glow">LEVEL 2 — PREMIUM</h2>
          <p className="font-mono text-2xl">$19<span className="text-sm text-muted">/mo</span></p>
          <ul className="font-mono text-xs space-y-2">
            <li>◉ Unlimited watchlist</li>
            <li>◉ Realtime alert feed</li>
            <li>◉ Email intel briefings</li>
            <li>◉ Full price history</li>
            <li>◉ AI news radar</li>
          </ul>
          <button
            type="button"
            onClick={checkout}
            disabled={loading}
            className="font-mono text-sm bg-accent text-background px-4 py-2 w-full hover:bg-accent-dim disabled:opacity-50 tracking-wider"
          >
            {loading ? "PROCESSING..." : "ACTIVATE PREMIUM"}
          </button>
        </div>
      </div>

      {error && <p className="font-mono text-xs text-alert-increase">{error}</p>}

      <Link href="/" className="font-mono text-xs text-muted hover:text-accent">
        ← BACK
      </Link>
    </main>
  );
}
