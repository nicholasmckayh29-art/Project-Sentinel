"use client";

import type { Alert } from "@/lib/market-types";

export function LeaderCard({ alert }: { alert: Alert | null }) {
  if (!alert) {
    return (
      <div className="card-terminal p-4">
        <h3 className="font-mono text-xs text-accent tracking-widest mb-2">LEADER SIGNAL</h3>
        <p className="font-mono text-xs text-muted">&gt; NO RECENT ALERTS FOR SELECTION</p>
      </div>
    );
  }

  return (
    <div className="card-terminal p-4 space-y-2">
      <h3 className="font-mono text-xs text-accent tracking-widest">LEADER SIGNAL</h3>
      <p className="font-mono text-sm">{alert.display_name ?? alert.model_id}</p>
      <div className="grid grid-cols-2 gap-2 font-mono text-xs">
        <div>
          <span className="text-muted">TRUE COST</span>
          <p>${alert.true_cost?.toFixed(4) ?? "—"}/1K</p>
        </div>
        <div>
          <span className="text-muted">VS LEADER</span>
          <p className="text-alert-drop">
            {alert.savings_vs_leader_pct !== null && alert.savings_vs_leader_pct !== undefined
              ? `${alert.savings_vs_leader_pct.toFixed(1)}% savings`
              : "—"}
          </p>
        </div>
        {alert.leader_model_id && (
          <div className="col-span-2">
            <span className="text-muted">LEADER</span>
            <p>{alert.leader_model_id}</p>
          </div>
        )}
      </div>
    </div>
  );
}
