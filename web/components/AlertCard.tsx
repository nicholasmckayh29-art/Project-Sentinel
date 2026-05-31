import type { Alert } from "@/lib/market-types";

export function AlertCard({ alert }: { alert: Alert }) {
  const isDrop = alert.direction === "drop";
  const arrow = isDrop ? "▼" : "▲";
  const color = isDrop ? "text-alert-drop" : "text-alert-increase";
  const meta = alert.metadata ?? {};
  const action =
    (meta.action as string) ??
    (alert.savings_vs_leader_pct && alert.savings_vs_leader_pct > 10
      ? "Consider switching workload routing"
      : "Monitor for confirmation");

  return (
    <article className="card-terminal p-4 space-y-2">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <span className="badge-classified">[ SIGNAL ]</span>
        <span className="font-mono text-xs text-muted">
          {new Date(alert.created_at).toLocaleString()}
        </span>
      </div>
      <h3 className={`font-mono text-lg ${color} terminal-glow`}>
        {arrow} {alert.display_name ?? alert.model_id}
      </h3>
      <p className="font-mono text-sm text-muted">
        {alert.workload_name ?? "—"} · {alert.reason.replace(/_/g, " ")}
      </p>
      <div className="grid grid-cols-2 gap-2 font-mono text-xs">
        <div>
          <span className="text-muted">CHANGE</span>
          <p className={color}>{alert.pct_change?.toFixed(1)}%</p>
        </div>
        <div>
          <span className="text-muted">TRUE COST</span>
          <p>${alert.true_cost?.toFixed(4) ?? "—"}/1K</p>
        </div>
        <div>
          <span className="text-muted">BASELINE</span>
          <p>${alert.baseline_true_cost?.toFixed(4) ?? "—"}/1K</p>
        </div>
        <div>
          <span className="text-muted">VS LEADER</span>
          <p className="text-alert-drop">
            {alert.savings_vs_leader_pct != null
              ? `${alert.savings_vs_leader_pct.toFixed(1)}%`
              : "—"}
          </p>
        </div>
        {alert.leader_model_id && (
          <div className="col-span-2">
            <span className="text-muted">LEADER</span>
            <p>{alert.leader_model_id}</p>
          </div>
        )}
        <div className="col-span-2">
          <span className="text-muted">ACTION</span>
          <p>{action}</p>
        </div>
      </div>
    </article>
  );
}
