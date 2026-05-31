"use client";

import { computeSentiment, type SentimentBreakdown } from "@/lib/sentiment";
import type { MarketEvent } from "@/lib/market-types";
import { useMemo } from "react";

function Gauge({ breakdown }: { breakdown: SentimentBreakdown }) {
  const color =
    breakdown.label === "bullish"
      ? "text-alert-drop"
      : breakdown.label === "bearish"
        ? "text-alert-increase"
        : "text-muted";

  return (
    <div className="card-terminal p-4 flex flex-wrap items-center gap-6">
      <div>
        <p className="font-mono text-[10px] text-muted tracking-widest">SENTIMENT · DERIVED FROM PUBLIC SOURCES</p>
        <p className={`font-mono text-3xl ${color} terminal-glow`}>{breakdown.score}</p>
        <p className={`font-mono text-xs uppercase ${color}`}>{breakdown.label}</p>
      </div>
      <div className="flex gap-4 font-mono text-xs">
        <div>
          <span className="text-muted">BULL</span>
          <p className="text-alert-drop">{breakdown.bullish}</p>
        </div>
        <div>
          <span className="text-muted">NEUT</span>
          <p>{breakdown.neutral}</p>
        </div>
        <div>
          <span className="text-muted">BEAR</span>
          <p className="text-alert-increase">{breakdown.bearish}</p>
        </div>
        {breakdown.hnAvg !== null && (
          <div>
            <span className="text-muted">HN AVG</span>
            <p>{breakdown.hnAvg.toFixed(0)}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export function SentimentPanel({ events }: { events: MarketEvent[] }) {
  const breakdown = useMemo(() => computeSentiment(events), [events]);
  return <Gauge breakdown={breakdown} />;
}

export function SentimentPanelFromBreakdown({ breakdown }: { breakdown: SentimentBreakdown }) {
  return <Gauge breakdown={breakdown} />;
}
