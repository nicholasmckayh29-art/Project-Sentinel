"use client";

import type { MacroSnapshot } from "@/lib/market-types";

export function MacroBar({ snapshots }: { snapshots: MacroSnapshot[] }) {
  if (snapshots.length === 0) return null;

  return (
    <div className="border border-border bg-surface px-4 py-2 flex flex-wrap gap-6 font-mono text-xs">
      <span className="text-muted tracking-widest">MACRO</span>
      {snapshots.map((s) => (
        <span key={s.series_id}>
          <span className="text-accent">{s.label}</span>{" "}
          {s.value?.toFixed(2) ?? "—"}
          {s.change_pct !== null && (
            <span className={s.change_pct >= 0 ? "text-alert-drop ml-1" : "text-alert-increase ml-1"}>
              ({s.change_pct >= 0 ? "+" : ""}{s.change_pct}%)
            </span>
          )}
        </span>
      ))}
    </div>
  );
}
