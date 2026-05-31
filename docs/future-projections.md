# Future Projections — Design Document

> Status: **Not implemented**. This document describes intended behavior only.

## Monte Carlo price bands

### Goal

Visualize plausible future **output $/1M** ranges for watched models on DESK using historical `price_snapshots` — never as predictions.

### Method (planned)

1. Pull daily (or per-fetch) output prices for a model over 90d.
2. Compute log returns: `r_t = ln(P_t / P_{t-1})`.
3. Estimate μ (mean) and σ (std) of returns.
4. Simulate N paths (e.g. 500) over H days (e.g. 30) using log-normal draws.
5. Plot fan chart: p10, p50, p90 bands.

### UI requirements

- Panel title: **SIMULATED PRICE BANDS**
- Subtitle: "Based on historical volatility. Not a forecast."
- Distinct styling from live price line (dashed / muted green).

### Data dependencies

- `price_snapshots` with sufficient history (post-backfill).
- Client-side Recharts or server-rendered QuickChart PNG for email.

## Routing projection overlay (Phase 2+)

Combine routing recommendations with Monte Carlo to show "cost at p50" per route — still labeled simulated.

## Open questions

- Minimum snapshot count before showing bands (suggest ≥ 14 points).
- Handle price drops to zero (floor at small epsilon in log space).
