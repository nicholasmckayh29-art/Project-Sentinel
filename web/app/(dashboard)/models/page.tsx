import { PriceSparkline, PeriodChangeBadge } from "@/components/PriceSparkline";
import {
  computePeriodChange,
  groupSnapshotsByModel,
  outputPriceSeries,
} from "@/lib/price-trends";
import { createClient } from "@/lib/supabase/server";

const HISTORY_DAYS = 90;

export default async function ModelsPage() {
  const supabase = await createClient();
  const since = new Date();
  since.setDate(since.getDate() - HISTORY_DAYS);

  const [{ data: models }, { data: snapshots }] = await Promise.all([
    supabase
      .from("models")
      .select("id, display_name, provider_id, pricing, benchmarks")
      .order("provider_id")
      .order("display_name"),
    supabase
      .from("price_snapshots")
      .select("model_id, fetched_at, output_per_1m")
      .gte("fetched_at", since.toISOString())
      .order("fetched_at", { ascending: true }),
  ]);

  const trendsByModel = groupSnapshotsByModel(snapshots ?? []);

  const grouped = (models ?? []).reduce<Record<string, typeof models>>((acc, m) => {
    if (!acc[m.provider_id]) acc[m.provider_id] = [];
    acc[m.provider_id]!.push(m);
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      <div>
        <p className="badge-classified inline-block mb-2">CATALOG</p>
        <h1 className="font-mono text-2xl text-accent terminal-glow">MODEL REGISTRY</h1>
        <p className="font-mono text-xs text-muted mt-1">
          Output $/1M trend · last {HISTORY_DAYS} days
        </p>
      </div>
      {Object.entries(grouped).map(([provider, items]) => (
        <section key={provider} className="space-y-2">
          <h2 className="font-mono text-sm text-accent tracking-widest uppercase">{provider}</h2>
          <div className="space-y-2">
            {items?.map((model) => {
              const points = trendsByModel.get(model.id) ?? [];
              const series = outputPriceSeries(points);
              const pct = computePeriodChange(points);

              return (
                <div
                  key={model.id}
                  className="card-terminal p-3 flex justify-between items-center gap-4 flex-wrap"
                >
                  <div className="min-w-0">
                    <span className="font-mono text-sm block">{model.display_name}</span>
                    <span className="font-mono text-xs text-muted">
                      IN ${model.pricing?.input_per_1m ?? "—"}/1M · OUT $
                      {model.pricing?.output_per_1m ?? "—"}/1M
                    </span>
                  </div>
                  <div className="flex items-center gap-4 shrink-0">
                    <PriceSparkline values={series} />
                    <PeriodChangeBadge pct={pct} />
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      ))}
      {(!models || models.length === 0) && (
        <p className="font-mono text-sm text-muted">
          &gt; NO MODELS IN DATABASE. RUN WORKER OR SEED SCRIPT.
        </p>
      )}
      {models && models.length > 0 && (!snapshots || snapshots.length === 0) && (
        <p className="font-mono text-xs text-muted border border-border p-3">
          &gt; NO PRICE HISTORY YET. RUN{" "}
          <code className="text-accent">python backend/engine/backfill_supabase.py --with-alerts</code>
        </p>
      )}
    </div>
  );
}
