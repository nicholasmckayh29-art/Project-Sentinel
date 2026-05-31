# Launch hygiene — operator checklist

## Stripe (production billing)

Set in Vercel / deployment environment:

- `STRIPE_SECRET_KEY` — live secret key from Stripe Dashboard
- `STRIPE_WEBHOOK_SECRET` — signing secret for `/api/stripe/webhook`
- `NEXT_PUBLIC_STRIPE_PRICE_ID` — premium subscription price ID

Verify checkout flow at `/pricing` → Stripe Checkout → webhook updates `subscriptions.status = active`.

## Premium Realtime gates

- **Alerts:** RLS delays non-premium alerts 24h; TERMINAL price tape Realtime INSERT only applies for premium users (`TerminalLayout`).
- **News:** `market_events` Realtime is open to all authenticated users.
- **History:** Migration `002` extends free tier to 90-day snapshots.

## External API keys (market sync)

Optional secrets for GitHub Actions `news-sync.yml`:

| Secret | Purpose |
|--------|---------|
| `FINNHUB_API_KEY` | Equity quotes (prod) |
| `FRED_API_KEY` | Macro strip |
| `DEVTO_API_KEY` | Dev.to articles |
| `MARKETAUX_API_KEY` | Ticker-tagged news |
| `GITHUB_TOKEN` | GitHub release polling |

HN, RSS, arXiv, OpenAlex, Bluesky, yfinance (dev), Hugging Face public endpoints need no keys.

## Cron workflows

- `price-sync.yml` — weekdays 9:00 UTC
- `news-sync.yml` — every 6 hours
- `routing-sync.yml` — Mondays 10:00 UTC

## Migrations

Apply in order: `001` → `002` → `003` → `004` → `005` → `006`.

Then run backfill if sparklines are empty:

```bash
python backend/engine/backfill_supabase.py --with-alerts
python backend/market_sync_worker.py
```
