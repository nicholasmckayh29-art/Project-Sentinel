type PriceSparklineProps = {
  values: number[];
  width?: number;
  height?: number;
  className?: string;
};

export function PriceSparkline({
  values,
  width = 88,
  height = 28,
  className,
}: PriceSparklineProps) {
  if (values.length < 2) {
    return <span className="font-mono text-xs text-muted">—</span>;
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const pad = 2;
  const innerW = width - pad * 2;
  const innerH = height - pad * 2;

  const coords = values.map((v, i) => {
    const x = pad + (i / (values.length - 1)) * innerW;
    const y = pad + innerH - ((v - min) / range) * innerH;
    return `${x},${y}`;
  });

  const trend = values[values.length - 1]! - values[0]!;
  const stroke = trend <= 0 ? "var(--alert-drop)" : "var(--alert-increase)";

  return (
    <svg
      width={width}
      height={height}
      className={className}
      role="img"
      aria-label="Output price trend"
    >
      <polyline
        fill="none"
        stroke={stroke}
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeLinecap="round"
        points={coords.join(" ")}
      />
    </svg>
  );
}

type PeriodChangeBadgeProps = {
  pct: number | null;
  label?: string;
};

export function PeriodChangeBadge({ pct, label = "YTD" }: PeriodChangeBadgeProps) {
  if (pct === null) {
    return <span className="font-mono text-xs text-muted">—</span>;
  }

  const isDrop = pct <= 0;
  const color = isDrop ? "text-alert-drop" : "text-alert-increase";

  return (
    <span className={`font-mono text-xs ${color} whitespace-nowrap`}>
      <span className="text-muted mr-1">{label}</span>
      {isDrop ? "▼" : "▲"} {Math.abs(pct).toFixed(1)}%
    </span>
  );
}
