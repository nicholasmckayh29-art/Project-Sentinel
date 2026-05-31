import { createClient } from "@/lib/supabase/server";

export default async function ModelsPage() {
  const supabase = await createClient();
  const { data: models } = await supabase
    .from("models")
    .select("id, display_name, provider_id, pricing, benchmarks")
    .order("provider_id")
    .order("display_name");

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
      </div>
      {Object.entries(grouped).map(([provider, items]) => (
        <section key={provider} className="space-y-2">
          <h2 className="font-mono text-sm text-accent tracking-widest uppercase">{provider}</h2>
          <div className="space-y-2">
            {items?.map((model) => (
              <div key={model.id} className="card-terminal p-3 flex justify-between gap-4 flex-wrap">
                <span className="font-mono text-sm">{model.display_name}</span>
                <span className="font-mono text-xs text-muted">
                  IN ${model.pricing?.input_per_1m ?? "—"}/1M · OUT ${model.pricing?.output_per_1m ?? "—"}/1M
                </span>
              </div>
            ))}
          </div>
        </section>
      ))}
      {(!models || models.length === 0) && (
        <p className="font-mono text-sm text-muted">
          &gt; NO MODELS IN DATABASE. RUN WORKER OR SEED SCRIPT.
        </p>
      )}
    </div>
  );
}
