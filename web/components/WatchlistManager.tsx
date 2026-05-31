"use client";

import { WatchlistTrends } from "@/components/WatchlistTrends";
import { createClient } from "@/lib/supabase/client";
import { useCallback, useEffect, useState } from "react";

type Model = { id: string; display_name: string; provider_id: string };
type Provider = { id: string; display_name: string };
type Workload = { id: string; name: string };

export function WatchlistManager() {
  const [models, setModels] = useState<Model[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [workloads, setWorkloads] = useState<Workload[]>([]);
  const [watchedModels, setWatchedModels] = useState<Set<string>>(new Set());
  const [watchedProviders, setWatchedProviders] = useState<Set<string>>(new Set());
  const [watchedWorkloads, setWatchedWorkloads] = useState<Set<string>>(new Set());
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    const supabase = createClient();
    const [m, p, w, wm, wp, ww] = await Promise.all([
      supabase.from("models").select("id, display_name, provider_id").order("display_name"),
      supabase.from("providers").select("id, display_name").order("display_name"),
      supabase.from("workloads").select("id, name").order("name"),
      supabase.from("user_watchlist_models").select("model_id"),
      supabase.from("user_watchlist_providers").select("provider_id"),
      supabase.from("user_watchlist_workloads").select("workload_id"),
    ]);
    setModels(m.data ?? []);
    setProviders(p.data ?? []);
    setWorkloads(w.data ?? []);
    setWatchedModels(new Set((wm.data ?? []).map((r) => r.model_id)));
    setWatchedProviders(new Set((wp.data ?? []).map((r) => r.provider_id)));
    setWatchedWorkloads(new Set((ww.data ?? []).map((r) => r.workload_id)));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function toggle(
    table: "user_watchlist_models" | "user_watchlist_providers" | "user_watchlist_workloads",
    col: string,
    id: string,
    watched: Set<string>,
    setWatched: (s: Set<string>) => void
  ) {
    const supabase = createClient();
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return;

    if (watched.has(id)) {
      await supabase.from(table).delete().eq("user_id", user.id).eq(col, id);
      const next = new Set(watched);
      next.delete(id);
      setWatched(next);
    } else {
      const { error } = await supabase.from(table).insert({ user_id: user.id, [col]: id });
      if (error) {
        setMessage(error.message.includes("watchlist") ? "FREE TIER: 3 ITEMS MAX. UPGRADE FOR UNLIMITED." : error.message);
        return;
      }
      setWatched(new Set(watched).add(id));
    }
    setMessage(null);
  }

  return (
    <div className="space-y-8">
      {message && (
        <p className="font-mono text-xs text-alert-increase border border-alert-increase p-3">
          {message}
        </p>
      )}

      <section className="space-y-3">
        <h2 className="font-mono text-sm text-accent tracking-widest">PROVIDERS</h2>
        <div className="flex flex-wrap gap-2">
          {providers.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() =>
                toggle("user_watchlist_providers", "provider_id", p.id, watchedProviders, setWatchedProviders)
              }
              className={`font-mono text-xs px-3 py-1 border ${
                watchedProviders.has(p.id)
                  ? "border-accent text-accent bg-accent/10"
                  : "border-border text-muted hover:border-accent"
              }`}
            >
              {watchedProviders.has(p.id) ? "◉" : "○"} {p.display_name}
            </button>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="font-mono text-sm text-accent tracking-widest">MODELS</h2>
        <div className="grid gap-2 max-h-64 overflow-y-auto">
          {models.map((m) => (
            <button
              key={m.id}
              type="button"
              onClick={() =>
                toggle("user_watchlist_models", "model_id", m.id, watchedModels, setWatchedModels)
              }
              className={`font-mono text-xs text-left px-3 py-2 border ${
                watchedModels.has(m.id)
                  ? "border-accent text-accent bg-accent/10"
                  : "border-border text-muted hover:border-accent"
              }`}
            >
              {watchedModels.has(m.id) ? "◉" : "○"} {m.display_name}
              <span className="text-muted ml-2">({m.provider_id})</span>
            </button>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="font-mono text-sm text-accent tracking-widest">WORKLOAD PRESETS</h2>
        <div className="flex flex-wrap gap-2">
          {workloads.map((w) => (
            <button
              key={w.id}
              type="button"
              onClick={() =>
                toggle("user_watchlist_workloads", "workload_id", w.id, watchedWorkloads, setWatchedWorkloads)
              }
              className={`font-mono text-xs px-3 py-1 border ${
                watchedWorkloads.has(w.id)
                  ? "border-accent text-accent bg-accent/10"
                  : "border-border text-muted hover:border-accent"
              }`}
            >
              {watchedWorkloads.has(w.id) ? "◉" : "○"} {w.name}
            </button>
          ))}
        </div>
      </section>

      <WatchlistTrends
        watchedModelIds={Array.from(watchedModels)}
        models={models}
      />
    </div>
  );
}
