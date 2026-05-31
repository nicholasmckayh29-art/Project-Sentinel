export type SnapshotPoint = {
  fetched_at: string;
  output_per_1m: number;
};

export function groupSnapshotsByModel(
  snapshots: { model_id: string; fetched_at: string; output_per_1m: number }[]
): Map<string, SnapshotPoint[]> {
  const map = new Map<string, SnapshotPoint[]>();
  for (const s of snapshots) {
    const list = map.get(s.model_id) ?? [];
    list.push({ fetched_at: s.fetched_at, output_per_1m: s.output_per_1m });
    map.set(s.model_id, list);
  }
  for (const points of map.values()) {
    points.sort((a, b) => a.fetched_at.localeCompare(b.fetched_at));
  }
  return map;
}

/** Percent change from earliest to latest snapshot in the series. */
export function computePeriodChange(points: SnapshotPoint[]): number | null {
  if (points.length < 2) return null;
  const first = points[0]!.output_per_1m;
  const last = points[points.length - 1]!.output_per_1m;
  if (first <= 0) return null;
  return ((last - first) / first) * 100;
}

export function outputPriceSeries(points: SnapshotPoint[]): number[] {
  return points.map((p) => p.output_per_1m);
}
