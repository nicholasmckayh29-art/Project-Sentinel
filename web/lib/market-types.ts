export type MarketEvent = {
  id: string;
  title: string;
  summary: string | null;
  event_type: string;
  source: string | null;
  url: string | null;
  published_at: string;
  metadata?: Record<string, unknown>;
};

export type Alert = {
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
  savings_vs_leader_pct?: number | null;
  leader_model_id?: string | null;
  metadata?: Record<string, unknown>;
};

export type MarketQuote = {
  symbol: string;
  name: string;
  price: number | null;
  change_pct: number | null;
  fetched_at: string;
  metadata?: Record<string, unknown>;
};

export type MacroSnapshot = {
  series_id: string;
  label: string;
  value: number | null;
  change_pct: number | null;
  fetched_at: string;
};

export type CommunitySignal = {
  id: string;
  signal_type: string;
  label: string;
  value: number | null;
  metadata?: Record<string, unknown>;
  fetched_at: string;
};

export type ModelTick = {
  model_id: string;
  display_name: string;
  output_per_1m: number;
  change_pct: number | null;
};

export type SnapshotRow = {
  fetched_at: string;
  input_per_1m: number;
  output_per_1m: number;
};

export type RoutingRecommendation = {
  id: string;
  workload_id: string;
  models: { model: string; weight: number }[];
  projections: Record<string, number>;
  generated_at: string;
};
