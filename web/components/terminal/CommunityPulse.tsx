"use client";

import type { CommunitySignal } from "@/lib/market-types";

export function CommunityPulse({ signals }: { signals: CommunitySignal[] }) {
  const hf = signals.filter((s) => s.signal_type === "hf_trending").slice(0, 5);
  const jobs = signals.find((s) => s.signal_type === "ai_jobs_count");

  return (
    <div className="card-terminal p-4 space-y-3">
      <h3 className="font-mono text-xs text-accent tracking-widest">COMMUNITY PULSE</h3>
      {jobs && (
        <p className="font-mono text-xs">
          AI eng jobs in feed: <span className="text-accent">{jobs.value?.toFixed(0)}</span>
        </p>
      )}
      {hf.length === 0 ? (
        <p className="font-mono text-xs text-muted">&gt; NO HF TRENDING DATA</p>
      ) : (
        <ul className="space-y-1">
          {hf.map((s) => (
            <li key={s.id} className="font-mono text-xs flex justify-between gap-2">
              <span className="truncate">{s.label}</span>
              <span className="text-muted shrink-0">{s.value?.toLocaleString()} dl</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
