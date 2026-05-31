"use client";

import { MacroBar } from "@/components/terminal/MacroBar";
import { NewsWireLive } from "@/components/terminal/NewsWire";
import { PriceTapeLive, usePriceTapeAlerts } from "@/components/terminal/PriceTape";
import { SentimentPanel } from "@/components/terminal/SentimentPanel";
import { TickerTape } from "@/components/terminal/TickerTape";
import { createClient } from "@/lib/supabase/client";
import type {
  Alert,
  CommunitySignal,
  MacroSnapshot,
  MarketEvent,
  MarketQuote,
  ModelTick,
} from "@/lib/market-types";
import { useEffect, useState } from "react";

export function TerminalLayout({
  initialAlerts,
  initialNews,
  modelTicks,
  equityQuotes,
  macroSnapshots,
  communitySignals,
  isPremium = false,
}: {
  initialAlerts: Alert[];
  initialNews: MarketEvent[];
  modelTicks: ModelTick[];
  equityQuotes: MarketQuote[];
  macroSnapshots: MacroSnapshot[];
  communitySignals: CommunitySignal[];
  isPremium?: boolean;
}) {
  const { alerts, flashId: alertFlash, prepend: prependAlert } = usePriceTapeAlerts(initialAlerts);
  const [news, setNews] = useState(initialNews);
  const [newsFlashId, setNewsFlashId] = useState<string | null>(null);

  useEffect(() => {
    if (!newsFlashId) return;
    const t = setTimeout(() => setNewsFlashId(null), 1200);
    return () => clearTimeout(t);
  }, [newsFlashId]);

  useEffect(() => {
    const supabase = createClient();
    const channel = supabase
      .channel("terminal-feed")
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "alerts" },
        (payload) => {
          if (!isPremium) return;
          prependAlert(payload.new as Alert);
        }
      )
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "market_events" },
        (payload) => {
          const item = payload.new as MarketEvent;
          setNews((prev) => [item, ...prev].slice(0, 100));
          setNewsFlashId(item.id);
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [isPremium, prependAlert]);

  const jobsSignal = communitySignals.find((s) => s.signal_type === "ai_jobs_count");

  return (
    <div className="space-y-4">
      <TickerTape modelTicks={modelTicks} equityQuotes={equityQuotes} />

      <div className="grid lg:grid-cols-2 gap-4">
        <PriceTapeLive alerts={alerts} flashId={alertFlash} />
        <NewsWireLive news={news} flashId={newsFlashId} />
      </div>

      <SentimentPanel events={news} />
      <MacroBar snapshots={macroSnapshots} />

      {jobsSignal && (
        <p className="font-mono text-[10px] text-muted text-center">
          AI ENG JOB VELOCITY (DERIVED): {jobsSignal.value?.toFixed(0)} listings in feed
        </p>
      )}

      {!isPremium && (
        <p className="font-mono text-[10px] text-muted border border-border p-2">
          FREE TIER: Alerts delayed 24h. Upgrade for live price tape updates.
        </p>
      )}
    </div>
  );
}
