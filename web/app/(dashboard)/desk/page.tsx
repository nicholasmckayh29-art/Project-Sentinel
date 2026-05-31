import { DeskClient } from "@/components/terminal/DeskClient";
import { groupSnapshotsByModel } from "@/lib/price-trends";
import { mergeModelIds } from "@/lib/terminal-data";
import { createClient } from "@/lib/supabase/server";
import { Suspense } from "react";

const HISTORY_DAYS = 90;

export default async function DeskPage({
  searchParams,
}: {
  searchParams: Promise<{ models?: string }>;
}) {
  const params = await searchParams;
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  const since = new Date();
  since.setDate(since.getDate() - HISTORY_DAYS);

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

  let providerModelRows: { id: string; display_name: string; provider_id: string }[] = [];
  if (watchlistProviderIds.length > 0) {
    const { data } = await supabase
      .from("models")
      .select("id, display_name, provider_id")
      .in("provider_id", watchlistProviderIds);
    providerModelRows = data ?? [];
  }
  const effectiveModelIds = mergeModelIds(
    watchlistModelIds,
    providerModelRows.map((m) => m.id)
  );

  const selectedFromUrl = params.models?.split(",").filter(Boolean) ?? [];
  const selectedIds =
    selectedFromUrl.length > 0
      ? selectedFromUrl.slice(0, 3)
      : effectiveModelIds.slice(0, 3);

  const modelIdsToFetch =
    selectedIds.length > 0 ? selectedIds : effectiveModelIds;

  const [
    watchlistResult,
    { data: models },
    { data: snapshots },
    { data: alerts },
    { data: researchEvents },
    { data: communitySignals },
    { data: routesRaw },
  ] = await Promise.all([
    user
      ? supabase
          .from("user_watchlist_models")
          .select("model_id, models(id, display_name, provider_id, pricing)")
          .eq("user_id", user.id)
      : Promise.resolve({ data: [] as { model_id: string; models: { id: string; display_name: string; provider_id: string } | null }[] }),
    supabase.from("models").select("id, display_name, pricing"),
    modelIdsToFetch.length > 0
      ? supabase
          .from("price_snapshots")
          .select("model_id, fetched_at, input_per_1m, output_per_1m")
          .in("model_id", modelIdsToFetch)
          .gte("fetched_at", since.toISOString())
          .order("fetched_at", { ascending: true })
      : Promise.resolve({ data: [] as { model_id: string; fetched_at: string; input_per_1m: number; output_per_1m: number }[] }),
    selectedIds.length > 0
      ? supabase
          .from("alerts")
          .select("*")
          .in("model_id", selectedIds)
          .order("created_at", { ascending: false })
          .limit(1)
      : Promise.resolve({ data: [] as Record<string, unknown>[] }),
    supabase
      .from("market_events")
      .select("*")
      .in("event_type", ["research", "release"])
      .order("published_at", { ascending: false })
      .limit(20),
    supabase
      .from("community_signals")
      .select("*")
      .order("fetched_at", { ascending: false })
      .limit(20),
    supabase
      .from("routing_recommendations")
      .select("*")
      .order("generated_at", { ascending: false })
      .limit(10),
  ]);

  const watchlistRows = watchlistResult.data;

  const watchlistModels = (() => {
    const byId = new Map<string, { model_id: string; display_name: string; provider_id: string }>();
    for (const row of watchlistRows ?? []) {
      const m = row.models as { id: string; display_name: string; provider_id: string } | null;
      if (m) byId.set(m.id, { model_id: m.id, display_name: m.display_name, provider_id: m.provider_id });
    }
    for (const m of providerModelRows) {
      if (!byId.has(m.id)) {
        byId.set(m.id, { model_id: m.id, display_name: m.display_name, provider_id: m.provider_id });
      }
    }
    return [...byId.values()];
  })();

  const modelsById: Record<string, { id: string; display_name: string; pricing: { input_per_1m?: number; output_per_1m?: number } }> = {};
  for (const m of models ?? []) {
    modelsById[m.id] = m;
  }

  const trends = groupSnapshotsByModel(snapshots ?? []);
  const primaryId = selectedIds[0];
  const primaryPoints = primaryId ? trends.get(primaryId) ?? [] : [];

  const lineData = primaryPoints.map((p) => ({
    date: new Date(p.fetched_at).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
    output: p.output_per_1m,
  }));

  const barData = selectedIds.map((id) => {
    const m = modelsById[id];
    const points = trends.get(id) ?? [];
    const latest = points[points.length - 1];
    return {
      name: m?.display_name?.slice(0, 12) ?? id.slice(0, 12),
      output: latest?.output_per_1m ?? m?.pricing?.output_per_1m ?? 0,
    };
  });

  const tableRows = (snapshots ?? []).map((s, i, arr) => {
    const prev = arr[i - 1];
    let delta_pct: number | null = null;
    if (prev && prev.model_id === s.model_id && prev.output_per_1m > 0) {
      delta_pct = ((s.output_per_1m - prev.output_per_1m) / prev.output_per_1m) * 100;
    }
    return { ...s, delta_pct };
  }).reverse();

  const workloadRoutes = new Map<string, typeof routesRaw>();
  for (const r of routesRaw ?? []) {
    if (!workloadRoutes.has(r.workload_id)) {
      workloadRoutes.set(r.workload_id, []);
    }
    workloadRoutes.get(r.workload_id)!.push(r);
  }
  const routes = Array.from(workloadRoutes.values())
    .map((group) => group![0])
    .filter(Boolean)
    .filter((r) =>
      watchlistWorkloadIds.length === 0 ? true : watchlistWorkloadIds.includes(r.workload_id)
    )
    .slice(0, 3);

  return (
    <div className="space-y-4">
      <div>
        <p className="badge-classified inline-block mb-2">COMMAND CENTER</p>
        <h1 className="font-mono text-2xl text-accent terminal-glow">DESK</h1>
        <p className="text-sm text-muted mt-1">
          Select models, view the same data through multiple lenses.
        </p>
      </div>
      <Suspense fallback={<p className="font-mono text-xs text-muted">Loading desk…</p>}>
        <DeskClient
          watchlistModels={watchlistModels}
          selectedIds={selectedIds}
          modelsById={modelsById}
          lineData={lineData}
          barData={barData}
          tableRows={tableRows}
          latestAlert={(alerts?.[0] as never) ?? null}
          researchEvents={researchEvents ?? []}
          communitySignals={communitySignals ?? []}
          routes={routes as never}
          hasSnapshots={(snapshots?.length ?? 0) > 0}
        />
      </Suspense>
    </div>
  );
}
