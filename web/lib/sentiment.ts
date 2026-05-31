import type { MarketEvent } from "@/lib/market-types";

const BULLISH = /\b(benchmark|sota|breakthrough|launch|funding)\b/i;
const BEARISH = /\b(price cut|layoff|regulation|ban|safety concern)\b/i;

export type SentimentBreakdown = {
  score: number;
  label: "bullish" | "neutral" | "bearish";
  bullish: number;
  neutral: number;
  bearish: number;
  hnAvg: number | null;
};

export function computeSentiment(events: MarketEvent[]): SentimentBreakdown {
  if (events.length === 0) {
    return { score: 50, label: "neutral", bullish: 0, neutral: 0, bearish: 0, hnAvg: null };
  }

  let bullish = 0;
  let neutral = 0;
  let bearish = 0;
  let hnTotal = 0;
  let hnCount = 0;

  for (const event of events) {
    const meta = event.metadata ?? {};
    const hint = (meta.sentiment_hint as string) ?? "";
    const text = `${event.title} ${event.summary ?? ""}`;

    if (hint === "bullish" || BULLISH.test(text)) bullish += 1;
    else if (hint === "bearish" || BEARISH.test(text)) bearish += 1;
    else neutral += 1;

    const hn = meta.hn_points as number | undefined;
    if (typeof hn === "number") {
      hnTotal += hn;
      hnCount += 1;
    }

    const reddit = meta.reddit_score as number | undefined;
    if (typeof reddit === "number") {
      hnTotal += Math.min(reddit, 500);
      hnCount += 1;
    }
  }

  const total = bullish + neutral + bearish || 1;
  const mixScore = ((bullish / total) * 100 + (neutral / total) * 50) / 1;
  const hnAvg = hnCount > 0 ? hnTotal / hnCount : null;
  const hnScore = hnAvg !== null ? Math.min(100, (hnAvg / 300) * 100) : 50;
  const score = Math.round(hnCount > 0 ? mixScore * 0.6 + hnScore * 0.4 : mixScore);

  let label: SentimentBreakdown["label"] = "neutral";
  if (score >= 60) label = "bullish";
  else if (score <= 40) label = "bearish";

  return { score, label, bullish, neutral, bearish, hnAvg };
}
