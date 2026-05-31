"use client";

import type { Alert } from "@/lib/market-types";
import { useEffect, useState } from "react";

function CompactAlertRow({ alert, flash }: { alert: Alert; flash: boolean }) {
  const isDrop = alert.direction === "drop";
  const color = isDrop ? "text-alert-drop" : "text-alert-increase";
  const arrow = isDrop ? "▼" : "▲";

  return (
    <div
      className={`grid grid-cols-[1fr_auto_auto] gap-3 px-3 py-2 border-b border-border font-mono text-xs items-center transition-colors ${
        flash ? "bg-surface-elevated" : ""
      }`}
    >
      <span className="truncate">{alert.display_name ?? alert.model_id}</span>
      <span className={color}>
        {arrow} {alert.pct_change?.toFixed(1) ?? "—"}%
      </span>
      <span className="text-muted">{new Date(alert.created_at).toLocaleTimeString()}</span>
    </div>
  );
}

export function PriceTape({ initialAlerts }: { initialAlerts: Alert[] }) {
  const [alerts, setAlerts] = useState(initialAlerts);
  const [flashId, setFlashId] = useState<string | null>(null);

  useEffect(() => {
    if (!flashId) return;
    const t = setTimeout(() => setFlashId(null), 1200);
    return () => clearTimeout(t);
  }, [flashId]);

  return (
    <div className="card-terminal h-full flex flex-col min-h-[280px]">
      <div className="px-3 py-2 border-b border-border">
        <h2 className="font-mono text-xs text-accent tracking-widest">PRICE TAPE</h2>
      </div>
      <div className="flex-1 overflow-y-auto max-h-[420px]">
        {alerts.length === 0 ? (
          <p className="font-mono text-xs text-muted p-3">&gt; NO SIGNALS</p>
        ) : (
          alerts.map((alert) => (
            <CompactAlertRow key={alert.id} alert={alert} flash={flashId === alert.id} />
          ))
        )}
      </div>
    </div>
  );
}

export function usePriceTapeAlerts(
  initialAlerts: Alert[],
  onNewAlert?: (alert: Alert) => void
) {
  const [alerts, setAlerts] = useState(initialAlerts);
  const [flashId, setFlashId] = useState<string | null>(null);

  const prepend = (alert: Alert) => {
    setAlerts((prev) => [alert, ...prev].slice(0, 100));
    setFlashId(alert.id);
    onNewAlert?.(alert);
  };

  return { alerts, flashId, prepend, setAlerts };
}

export function PriceTapeLive({
  alerts,
  flashId,
}: {
  alerts: Alert[];
  flashId: string | null;
}) {
  return (
    <div className="card-terminal h-full flex flex-col min-h-[280px]">
      <div className="px-3 py-2 border-b border-border">
        <h2 className="font-mono text-xs text-accent tracking-widest">PRICE TAPE</h2>
      </div>
      <div className="flex-1 overflow-y-auto max-h-[420px]">
        {alerts.length === 0 ? (
          <p className="font-mono text-xs text-muted p-3">&gt; NO SIGNALS</p>
        ) : (
          alerts.map((alert) => (
            <CompactAlertRow key={alert.id} alert={alert} flash={flashId === alert.id} />
          ))
        )}
      </div>
    </div>
  );
}
