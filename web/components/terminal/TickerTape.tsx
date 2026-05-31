"use client";

import type { MarketQuote, ModelTick } from "@/lib/market-types";

function TickItem({
  label,
  value,
  changePct,
  prefix = "",
}: {
  label: string;
  value: string;
  changePct: number | null;
  prefix?: string;
}) {
  const up = changePct !== null && changePct >= 0;
  const color = changePct === null ? "text-muted" : up ? "text-alert-drop" : "text-alert-increase";
  const arrow = changePct === null ? "" : up ? "▲" : "▼";

  return (
    <span className="inline-flex items-center gap-2 px-4 font-mono text-xs whitespace-nowrap">
      <span className="text-accent">{label}</span>
      <span>{prefix}{value}</span>
      {changePct !== null && (
        <span className={color}>
          {arrow} {Math.abs(changePct).toFixed(1)}%
        </span>
      )}
    </span>
  );
}

export function TickerTape({
  modelTicks,
  equityQuotes,
}: {
  modelTicks: ModelTick[];
  equityQuotes: MarketQuote[];
}) {
  const modelItems = modelTicks.map((t) => (
    <TickItem
      key={t.model_id}
      label={t.display_name}
      value={`$${t.output_per_1m.toFixed(2)}/1M`}
      changePct={t.change_pct}
    />
  ));

  const equityItems = equityQuotes.map((q) => (
    <TickItem
      key={q.symbol}
      label={q.symbol}
      value={q.price?.toFixed(2) ?? "—"}
      changePct={q.change_pct}
      prefix="$"
    />
  ));

  const lane1 = modelItems.length > 0 ? modelItems : [
    <span key="empty-models" className="px-4 font-mono text-xs text-muted">NO WATCHED MODELS</span>,
  ];
  const lane2 = equityItems.length > 0 ? equityItems : [
    <span key="empty-equity" className="px-4 font-mono text-xs text-muted">EQUITY DATA PENDING</span>,
  ];

  return (
    <div className="border border-border bg-surface overflow-hidden space-y-0">
      <div className="border-b border-border py-1.5 overflow-hidden">
        <div className="ticker-marquee flex">{lane1}{lane1}</div>
      </div>
      <div className="py-1.5 overflow-hidden opacity-90">
        <div className="ticker-marquee-reverse flex">{lane2}{lane2}</div>
      </div>
    </div>
  );
}
