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

export function AlertCard({ alert }: { alert: Alert }) {
  const isDrop = alert.direction === "drop";
  const arrow = isDrop ? "▼" : "▲";
  const color = isDrop ? "text-alert-drop" : "text-alert-increase";

  return (
    <article className="card-terminal p-4 space-y-2">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <span className="badge-classified">[ CLASSIFIED ]</span>
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
          <span className="text-muted">PRIORITY</span>
          <p className="uppercase">{alert.priority}</p>
        </div>
      </div>
    </article>
  );
}
