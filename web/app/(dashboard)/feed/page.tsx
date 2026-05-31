import { TerminalLayout } from "@/components/terminal/TerminalLayout";
import { buildModelTicks, filterAlertsByScope, getPremiumStatus, mergeModelIds } from "@/lib/terminal-data";
import { createClient } from "@/lib/supabase/server";

export default async function FeedPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  const isPremium = await getPremiumStatus(supabase);

  let watchlistModelIds: string[] = [];
  let watchlistProviderIds: string[] = [];
  let watchlistWorkloadIds: string[] = [];
  if (user) {
    const [{ data: wl }, { data: wp }, { data: ww }] = await Promise.all([
      supabase.from("user_watchlist_models").select("model_id").eq("user_id", user.id),
      supabase.from("user_watchlist_providers").select("provider_id").eq("user_id", user.id),
      supabase.from("user_watchlist_workloads").select("workload_id").eq("user_id", user.id),
    ]);
    watchlistModelIds = (wl ?? []).map((r) => r.model_id);
    watchlistProviderIds = (wp ?? []).map((r) => r.provider_id);
    watchlistWorkloadIds = (ww ?? []).map((r) => r.workload_id);
  }

  let providerModelIds: string[] = [];
  if (watchlistProviderIds.length > 0) {
    const { data: providerModels } = await supabase
      .from("models")
      .select("id")
      .in("provider_id", watchlistProviderIds);
    providerModelIds = (providerModels ?? []).map((m) => m.id);
  }
  const effectiveModelIds = mergeModelIds(watchlistModelIds, providerModelIds);
  const hasWatchlist =
    effectiveModelIds.length > 0 || watchlistWorkloadIds.length > 0;

  const since = new Date();
  since.setDate(since.getDate() - 90);

  const idsForTicks = effectiveModelIds.length > 0 ? effectiveModelIds : null;

  const [
    { data: alertsRaw },
    { data: news },
    { data: quotes },
    { data: macro },
    { data: community },
    { data: models },
    { data: snapshots },
  ] = await Promise.all([
    supabase.from("alerts").select("*").order("created_at", { ascending: false }).limit(50),
    supabase.from("market_events").select("*").order("published_at", { ascending: false }).limit(40),
    supabase.from("market_quotes").select("*").order("fetched_at", { ascending: false }),
    supabase.from("macro_snapshots").select("*"),
    supabase.from("community_signals").select("*").order("fetched_at", { ascending: false }).limit(10),
    idsForTicks
      ? supabase.from("models").select("id, display_name, pricing").in("id", idsForTicks)
      : Promise.resolve({ data: [] as { id: string; display_name: string; pricing?: { output_per_1m?: number } }[] }),
    idsForTicks
      ? supabase
          .from("price_snapshots")
          .select("model_id, fetched_at, output_per_1m")
          .in("model_id", idsForTicks)
          .gte("fetched_at", since.toISOString())
          .order("fetched_at", { ascending: true })
      : Promise.resolve({ data: [] as { model_id: string; fetched_at: string; output_per_1m: number }[] }),
  ]);

  const alerts = hasWatchlist
    ? filterAlertsByScope(alertsRaw ?? [], effectiveModelIds, watchlistWorkloadIds)
    : (alertsRaw ?? []);
  const modelTicks =
    idsForTicks && models
      ? buildModelTicks(idsForTicks, models, snapshots ?? [])
      : [];

  const equityQuotes = (quotes ?? []).slice(0, 6);

  return (
    <div className="space-y-4">
      <div>
        <p className="badge-classified inline-block mb-2">LIVE TERMINAL</p>
        <h1 className="font-mono text-2xl text-accent terminal-glow">TERMINAL</h1>
        <p className="text-sm text-muted mt-1">
          Price tape, news wire, equity strip, and derived sentiment.
        </p>
      </div>
      <TerminalLayout
        initialAlerts={alerts as never}
        initialNews={news ?? []}
        modelTicks={modelTicks}
        equityQuotes={equityQuotes as never}
        macroSnapshots={macro ?? []}
        communitySignals={community ?? []}
        isPremium={isPremium}
      />
    </div>
  );
}
