"use client";

import { PriceSparkline, PeriodChangeBadge } from "@/components/PriceSparkline";
import { createClient } from "@/lib/supabase/client";
import {
  computePeriodChange,
  groupSnapshotsByModel,
  outputPriceSeries,
  type SnapshotPoint,
} from "@/lib/price-trends";
import { useEffect, useState } from "react";

type Model = { id: string; display_name: string; provider_id: string };

const HISTORY_DAYS = 90;

export function WatchlistTrends({
  watchedModelIds,
  models,
}: {
  watchedModelIds: string[];
  models: Model[];
}) {
  const [trends, setTrends] = useState<Map<string, SnapshotPoint[]>>(new Map());
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (watchedModelIds.length === 0) {
      setTrends(new Map());
      return;
    }

    let cancelled = false;
    setLoading(true);

    (async () => {
      const supabase = createClient();
      const since = new Date();
      since.setDate(since.getDate() - HISTORY_DAYS);

      const { data } = await supabase
        .from("price_snapshots")
        .select("model_id, fetched_at, output_per_1m")
        .in("model_id", watchedModelIds)
        .gte("fetched_at", since.toISOString())
        .order("fetched_at", { ascending: true });

      if (!cancelled) {
        setTrends(groupSnapshotsByModel(data ?? []));
        setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [watchedModelIds.join(",")]);

  const watched = models.filter((m) => watchedModelIds.includes(m.id));

  if (watchedModelIds.length === 0) {
    return null;
  }

  return (
    <section className="space-y-3">
      <h2 className="font-mono text-sm text-accent tracking-widest">TRACKED MODEL TRENDS</h2>
      {loading && (
        <p className="font-mono text-xs text-muted animate-pulse">&gt; LOADING PRICE HISTORY…</p>
      )}
      <div className="space-y-2">
        {watched.map((model) => {
          const points = trends.get(model.id) ?? [];
          const series = outputPriceSeries(points);
          const pct = computePeriodChange(points);

          return (
            <div
              key={model.id}
              className="card-terminal p-3 flex justify-between items-center gap-4 flex-wrap"
            >
              <div>
                <span className="font-mono text-sm">{model.display_name}</span>
                <span className="font-mono text-xs text-muted ml-2">({model.provider_id})</span>
              </div>
              <div className="flex items-center gap-4 shrink-0">
                <PriceSparkline values={series} />
                <PeriodChangeBadge pct={pct} />
              </div>
            </div>
          );
        })}
      </div>
      {!loading && watched.length > 0 && trends.size === 0 && (
        <p className="font-mono text-xs text-muted">
          &gt; NO HISTORY FOR WATCHED MODELS. RUN BACKFILL OR WAIT FOR DAILY WORKER.
        </p>
      )}
    </section>
  );
}
