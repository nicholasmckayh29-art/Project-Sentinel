"use client";

import { BarComparePanel } from "@/components/terminal/charts/BarComparePanel";
import { LineChartPanel } from "@/components/terminal/charts/LineChartPanel";
import { PieCostPanel } from "@/components/terminal/charts/PieCostPanel";
import { SnapshotTable } from "@/components/terminal/charts/SnapshotTable";
import { CommunityPulse } from "@/components/terminal/CommunityPulse";
import { LeaderCard } from "@/components/terminal/LeaderCard";
import { ModelPicker } from "@/components/terminal/ModelPicker";
import { ResearchWire } from "@/components/terminal/NewsWire";
import { RoutePanel } from "@/components/terminal/RoutePanel";
import type {
  Alert,
  CommunitySignal,
  MarketEvent,
  RoutingRecommendation,
  SnapshotRow,
} from "@/lib/market-types";

type WatchlistModel = {
  model_id: string;
  display_name: string;
  provider_id: string;
};

type ModelMeta = {
  id: string;
  display_name: string;
  pricing: { input_per_1m?: number; output_per_1m?: number };
};

export function DeskClient({
  watchlistModels,
  selectedIds,
  modelsById,
  lineData,
  barData,
  tableRows,
  latestAlert,
  researchEvents,
  communitySignals,
  routes,
  hasSnapshots,
}: {
  watchlistModels: WatchlistModel[];
  selectedIds: string[];
  modelsById: Record<string, ModelMeta>;
  lineData: { date: string; output: number }[];
  barData: { name: string; output: number }[];
  tableRows: (SnapshotRow & { model_id: string; delta_pct?: number | null })[];
  latestAlert: Alert | null;
  researchEvents: MarketEvent[];
  communitySignals: CommunitySignal[];
  routes: RoutingRecommendation[];
  hasSnapshots: boolean;
}) {
  const primaryId = selectedIds[0];
  const primary = primaryId ? modelsById[primaryId] : null;
  const latestPrimary = primaryId ? tableRows.find((r) => r.model_id === primaryId) : undefined;

  return (
    <div className="space-y-6">
      <ModelPicker models={watchlistModels} selected={selectedIds} />

      {!hasSnapshots && (
        <p className="font-mono text-xs text-muted border border-border p-3">
          &gt; NO PRICE HISTORY YET. RUN BACKFILL FOR CHART DATA.
        </p>
      )}

      <div className="grid md:grid-cols-2 gap-4">
        <LineChartPanel
          data={lineData}
          title={primary ? `${primary.display_name} · OUTPUT $/1M · 90D` : "OUTPUT $/1M · 90D"}
        />
        <PieCostPanel
          inputPer1m={latestPrimary?.input_per_1m ?? primary?.pricing?.input_per_1m ?? 0}
          outputPer1m={latestPrimary?.output_per_1m ?? primary?.pricing?.output_per_1m ?? 0}
          title={primary ? `${primary.display_name} · COST MIX` : "COST MIX"}
        />
        <BarComparePanel data={barData} title="CROSS-MODEL COMPARE" />
        <LeaderCard alert={latestAlert} />
      </div>

      <SnapshotTable rows={tableRows} title="DAILY SNAPSHOTS" />

      <div className="grid md:grid-cols-2 gap-4">
        <ResearchWire events={researchEvents} />
        <CommunityPulse signals={communitySignals} />
      </div>

      <RoutePanel routes={routes} />
    </div>
  );
}
