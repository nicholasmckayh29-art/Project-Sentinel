"use client";

import type { RoutingRecommendation } from "@/lib/market-types";

export function RoutePanel({ routes }: { routes: RoutingRecommendation[] }) {
  if (routes.length === 0) {
    return (
      <div className="card-terminal p-4">
        <h3 className="font-mono text-xs text-accent tracking-widest mb-2">RECOMMENDED ROUTE</h3>
        <p className="font-mono text-xs text-muted">&gt; RUN ROUTING SYNC TO POPULATE</p>
      </div>
    );
  }

  return (
    <div className="card-terminal p-4 space-y-4">
      <h3 className="font-mono text-xs text-accent tracking-widest">RECOMMENDED ROUTE</h3>
      {routes.map((route) => (
        <div key={route.id} className="space-y-2">
          <p className="font-mono text-xs text-muted uppercase">{route.workload_id}</p>
          <div className="flex h-3 overflow-hidden border border-border">
            {route.models.map((m, i) => (
              <div
                key={m.model}
                className="h-full"
                style={{
                  width: `${m.weight * 100}%`,
                  background: i === 0 ? "#00ff41" : "#2a2a2a",
                  opacity: i === 0 ? 0.85 : 1,
                }}
                title={`${m.model} ${(m.weight * 100).toFixed(0)}%`}
              />
            ))}
          </div>
          <ul className="font-mono text-xs space-y-0.5">
            {route.models.map((m) => (
              <li key={m.model}>
                {m.model} — {(m.weight * 100).toFixed(0)}%
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
