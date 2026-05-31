"use client";

import type { SnapshotRow } from "@/lib/market-types";
import { useMemo, useState } from "react";

type SortKey = "date" | "input" | "output" | "delta";

export function SnapshotTable({
  rows,
  title,
}: {
  rows: (SnapshotRow & { model_id?: string; delta_pct?: number | null })[];
  title: string;
}) {
  const [sortKey, setSortKey] = useState<SortKey>("date");
  const [asc, setAsc] = useState(false);

  const sorted = useMemo(() => {
    const copy = [...rows];
    copy.sort((a, b) => {
      let av: number | string = 0;
      let bv: number | string = 0;
      if (sortKey === "date") {
        av = a.fetched_at;
        bv = b.fetched_at;
      } else if (sortKey === "input") {
        av = a.input_per_1m;
        bv = b.input_per_1m;
      } else if (sortKey === "output") {
        av = a.output_per_1m;
        bv = b.output_per_1m;
      } else {
        av = a.delta_pct ?? 0;
        bv = b.delta_pct ?? 0;
      }
      if (av < bv) return asc ? -1 : 1;
      if (av > bv) return asc ? 1 : -1;
      return 0;
    });
    return copy;
  }, [rows, sortKey, asc]);

  function header(key: SortKey, label: string) {
    return (
      <button
        type="button"
        onClick={() => {
          if (sortKey === key) setAsc(!asc);
          else {
            setSortKey(key);
            setAsc(false);
          }
        }}
        className="font-mono text-[10px] text-muted hover:text-accent uppercase"
      >
        {label}{sortKey === key ? (asc ? " ↑" : " ↓") : ""}
      </button>
    );
  }

  return (
    <div className="card-terminal p-4 overflow-x-auto">
      <h3 className="font-mono text-xs text-accent tracking-widest mb-3">{title}</h3>
      {rows.length === 0 ? (
        <p className="font-mono text-xs text-muted">&gt; NO SNAPSHOTS</p>
      ) : (
        <table className="w-full font-mono text-xs">
          <thead>
            <tr className="text-left border-b border-border">
              <th className="pb-2 pr-4">{header("date", "Date")}</th>
              <th className="pb-2 pr-4">{header("input", "In $/1M")}</th>
              <th className="pb-2 pr-4">{header("output", "Out $/1M")}</th>
              <th className="pb-2">{header("delta", "Δ%")}</th>
            </tr>
          </thead>
          <tbody>
            {sorted.slice(0, 30).map((row, i) => (
              <tr key={`${row.fetched_at}-${i}`} className="border-b border-border/50">
                <td className="py-1.5 pr-4 text-muted">
                  {new Date(row.fetched_at).toLocaleDateString()}
                </td>
                <td className="py-1.5 pr-4">${row.input_per_1m.toFixed(2)}</td>
                <td className="py-1.5 pr-4">${row.output_per_1m.toFixed(2)}</td>
                <td className={`py-1.5 ${(row.delta_pct ?? 0) <= 0 ? "text-alert-drop" : "text-alert-increase"}`}>
                  {row.delta_pct !== null && row.delta_pct !== undefined
                    ? `${row.delta_pct.toFixed(1)}%`
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
