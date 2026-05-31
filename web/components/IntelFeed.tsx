"use client";

import { AlertCard } from "@/components/AlertCard";
import { createClient } from "@/lib/supabase/client";
import { useEffect, useState } from "react";

type Alert = {
  id: string;
  created_at: string;
  model_id: string;
  display_name: string | null;
  workload_name: string | null;
  direction: "drop" | "increase";
  priority: string;
  reason: string;
  pct_change: number | null;
  true_cost: number | null;
  baseline_true_cost: number | null;
};

type MarketEvent = {
  id: string;
  title: string;
  summary: string | null;
  event_type: string;
  published_at: string;
};

export function IntelFeed({
  initialAlerts,
  initialNews,
}: {
  initialAlerts: Alert[];
  initialNews: MarketEvent[];
}) {
  const [alerts, setAlerts] = useState(initialAlerts);
  const [news] = useState(initialNews);

  useEffect(() => {
    const supabase = createClient();
    const channel = supabase
      .channel("alerts-feed")
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "alerts" },
        (payload) => {
          setAlerts((prev) => [payload.new as Alert, ...prev].slice(0, 100));
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  return (
    <div className="space-y-8">
      <section className="space-y-4">
        <h2 className="font-mono text-sm text-accent tracking-widest">PRICE SIGNALS</h2>
        {alerts.length === 0 ? (
          <p className="font-mono text-sm text-muted">
            &gt; NO SIGNALS. MARKET QUIET. STANDING BY.
          </p>
        ) : (
          <div className="space-y-4">
            {alerts.map((alert) => (
              <AlertCard key={alert.id} alert={alert} />
            ))}
          </div>
        )}
      </section>

      <section className="space-y-4">
        <h2 className="font-mono text-sm text-accent tracking-widest">AI NEWS RADAR</h2>
        {news.length === 0 ? (
          <p className="font-mono text-sm text-muted">&gt; NO INTEL ON FILE.</p>
        ) : (
          <div className="space-y-3">
            {news.map((item) => (
              <article key={item.id} className="card-terminal p-4">
                <p className="badge-classified inline-block mb-2">{item.event_type.toUpperCase()}</p>
                <h3 className="font-mono text-sm">{item.title}</h3>
                {item.summary && (
                  <p className="text-sm text-muted mt-1">{item.summary}</p>
                )}
                <p className="font-mono text-xs text-muted mt-2">
                  {new Date(item.published_at).toLocaleString()}
                </p>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
