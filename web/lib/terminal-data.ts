import { computePeriodChange, groupSnapshotsByModel } from "@/lib/price-trends";
import type { ModelTick } from "@/lib/market-types";

export function buildModelTicks(
  watchlistModelIds: string[],
  models: { id: string; display_name: string; pricing?: { output_per_1m?: number } }[],
  snapshots: { model_id: string; fetched_at: string; output_per_1m: number }[]
): ModelTick[] {
  const trends = groupSnapshotsByModel(snapshots);
  const modelMap = new Map(models.map((m) => [m.id, m]));

  return watchlistModelIds
    .map((id) => {
      const model = modelMap.get(id);
      if (!model) return null;
      const points = trends.get(id) ?? [];
      const latest = points[points.length - 1];
      const output = latest?.output_per_1m ?? model.pricing?.output_per_1m ?? 0;
      return {
        model_id: id,
        display_name: model.display_name,
        output_per_1m: output,
        change_pct: computePeriodChange(points),
      };
    })
    .filter((t): t is ModelTick => t !== null);
}

export function filterAlertsByWatchlist<T extends { model_id: string }>(
  alerts: T[],
  watchlistModelIds: string[] | null
): T[] {
  if (!watchlistModelIds || watchlistModelIds.length === 0) return alerts;
  const set = new Set(watchlistModelIds);
  const filtered = alerts.filter((a) => set.has(a.model_id));
  return filtered.length > 0 ? filtered : alerts;
}

export async function getPremiumStatus(
  supabase: Awaited<ReturnType<typeof import("@/lib/supabase/server").createClient>>
): Promise<boolean> {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return false;
  const { data: sub } = await supabase
    .from("subscriptions")
    .select("status, current_period_end")
    .eq("user_id", user.id)
    .maybeSingle();
  if (!sub || sub.status !== "active") return false;
  if (sub.current_period_end && new Date(sub.current_period_end) < new Date()) return false;
  return true;
}
