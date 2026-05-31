"use client";

import { WatchlistManager } from "@/components/WatchlistManager";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function OnboardingPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  async function complete() {
    setLoading(true);
    const supabase = createClient();
    const { data: { user } } = await supabase.auth.getUser();
    if (user) {
      await supabase
        .from("profiles")
        .update({ onboarding_complete: true })
        .eq("id", user.id);
    }
    router.push("/feed");
  }

  return (
    <main className="flex-1 px-4 py-8 max-w-3xl mx-auto w-full space-y-6">
      <div>
        <p className="badge-classified inline-block mb-2">ONBOARDING</p>
        <h1 className="font-mono text-2xl text-accent terminal-glow">CONFIGURE SURVEILLANCE</h1>
        <p className="text-sm text-muted mt-1">
          Pick what to track. Free tier: 3 items total. Premium: unlimited.
        </p>
      </div>
      <WatchlistManager />
      <button
        type="button"
        onClick={complete}
        disabled={loading}
        className="font-mono text-sm bg-accent text-background px-6 py-3 hover:bg-accent-dim disabled:opacity-50 tracking-wider"
      >
        {loading ? "INITIALIZING..." : "ENTER INTEL FEED →"}
      </button>
    </main>
  );
}
