import { IntelFeed } from "@/components/IntelFeed";
import { createClient } from "@/lib/supabase/server";

export default async function FeedPage() {
  const supabase = await createClient();

  const { data: alerts } = await supabase
    .from("alerts")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(50);

  const { data: news } = await supabase
    .from("market_events")
    .select("*")
    .order("published_at", { ascending: false })
    .limit(20);

  return (
    <div className="space-y-4">
      <div>
        <p className="badge-classified inline-block mb-2">LIVE FEED</p>
        <h1 className="font-mono text-2xl text-accent terminal-glow">INTEL STREAM</h1>
        <p className="text-sm text-muted mt-1">
          Price drops, spikes, and market signals — workload-aware True Cost analysis.
        </p>
      </div>
      <IntelFeed initialAlerts={alerts ?? []} initialNews={news ?? []} />
    </div>
  );
}
