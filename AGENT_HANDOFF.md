# Pricing Sentinel — Agent Handoff

> **Date**: May 31, 2026  
> **Repo**: `/Users/nich/Projects/pricing-sentinel`  
> **GitHub**: [nicholasmckayh29-art/Project-Sentinel](https://github.com/nicholasmckayh29-art/Project-Sentinel)  
> **Branch**: `main`  
> **Latest pushed commit**: `c85eadc` — Resend auth email fix + Google login fallback  
> **Status**: Web app live on Vercel; Supabase seeded; auth working; GitHub Actions worker configured

---

## Executive Summary

**Pricing Sentinel** is an AI model **decision layer** — not a dashboard. It tells users which model to use, when, and why, using True Cost math, price-drop alerts, and workload-aware routing.

The product shipped as a **web-first monorepo** (Mr. Robot terminal UI) on **Supabase + Vercel**, with a Python intelligence engine and GitHub Actions cron. **iOS is Phase 2** (funded by web revenue).

The human operator has completed: Supabase setup, catalog seed (41 models), Vercel deploy, magic-link auth (via Resend SMTP), and GitHub Actions price sync.

---

## Live Infrastructure

| Service | Detail |
|---------|--------|
| **Supabase project** | `eamkkmlpphsimvznjjcf` (Sentinel Project, us-west-2) |
| **Supabase API URL** | `https://eamkkmlpphsimvznjjcf.supabase.co` |
| **GitHub** | `https://github.com/nicholasmckayh29-art/Project-Sentinel` |
| **Vercel** | Root directory = `web` (auto-deploy from `main`) |
| **Auth email** | Custom SMTP via **Resend** (Supabase → Authentication → SMTP) |
| **Cron** | GitHub Actions → `.github/workflows/price-sync.yml` (weekdays 9am UTC) |

**Do not commit**: `.env`, `web/.env.local`, service role keys, Stripe secrets, Resend keys.

---

## What Works Today

| Area | Status |
|------|--------|
| Magic-link login (+ Google button in code) | ✅ Working (Resend SMTP configured) |
| Onboarding watchlist (providers/models/workloads) | ✅ |
| Model registry (`/models`, 41 models) | ✅ |
| Intel feed (`/feed`, Realtime on `alerts`) | ✅ UI ready; empty until worker/alerts run |
| Watchlist CRUD with free-tier 3-item limit | ✅ |
| Stripe checkout routes | ✅ Code exists; **Stripe not fully wired in prod yet** |
| Python price hunter + True Cost | ✅ 35 tests passing |
| Supabase seed (`seed_supabase.py`) | ✅ |
| GitHub Actions worker | ✅ Human confirmed working |
| SQLite local history | ✅ Dev-only additive |
| Slack alert delivery | ✅ Code exists; optional secrets |
| YTD history backfill | ⚠️ **Scripts committed**; run on prod Supabase (human env vars) |
| Price sparklines in UI | ✅ `/models` + watchlist trends |
| Premium Stripe live mode | ❌ Not started |
| iOS app | ❌ Placeholder only (`mobile/README.md`) |

---

## Monorepo Layout

```
pricing-sentinel/
├── web/                    Next.js 16 App Router → Vercel
│   ├── app/                Pages: /, /login, /onboarding, /feed, /watchlist, /models, /settings, /pricing
│   ├── components/         Terminal UI (Scanlines, TerminalBoot, AlertCard, IntelFeed, WatchlistManager)
│   └── lib/supabase/       Auth SSR + middleware
├── backend/
│   ├── engine/             Core Python logic (fetch, alerts, routing, supabase sync)
│   ├── alerts/             Slack + email formatters
│   ├── api/                FastAPI dev server (not production path)
│   ├── worker.py           Production cron entrypoint → Supabase
│   └── tests/              pytest (35 tests)
├── supabase/
│   └── migrations/         001_initial_schema.sql (run manually in SQL editor)
├── packages/theme/         Shared Mr. Robot design tokens
├── mobile/                 iOS Phase 2 placeholder
├── docs/                   deployment.md, auth-email-resend.md, design-system.md, app-store-checklist.md
├── data/                   Local JSON seeds (current_prices, workloads, model_capabilities)
└── .github/workflows/      price-sync.yml
```

---

## Architecture

```
pricetoken.ai API
       ↓
GitHub Actions (backend/worker.py)  — weekdays 9am UTC
       ↓
Supabase Postgres (price_snapshots, alerts, baselines, models, …)
       ↓
Next.js on Vercel (reads via anon key + RLS)
       ↓
User browser (magic link auth, Realtime feed)
```

**Auth**: Supabase Auth (email OTP + optional Google OAuth).  
**Payments**: Stripe Checkout → webhook → `subscriptions` table (RLS gates premium).  
**Email alerts**: Resend (auth SMTP + optional premium alert emails from worker).

---

## Supabase Schema (key tables)

| Table | Purpose |
|-------|---------|
| `models`, `providers`, `workloads` | Catalog |
| `price_snapshots` | Time-series pricing (daily rows from worker + backfill) |
| `baselines` | Alert comparison baselines |
| `alerts` | Price drop/increase events |
| `market_events` | AI news (Routine 2 stub) |
| `profiles`, `subscriptions` | Users + Stripe premium |
| `user_watchlist_*` | Per-user tracking (models, providers, workloads) |

**RLS highlights**:
- Free users: 7-day price history, 24h delayed alerts, 3 watchlist items
- Premium (`subscriptions.status = 'active'`): full history, realtime alerts

Migration file: [`supabase/migrations/001_initial_schema.sql`](supabase/migrations/001_initial_schema.sql)

---

## Essential Commands

### Verify Supabase connection
```bash
export SUPABASE_URL=https://eamkkmlpphsimvznjjcf.supabase.co
export SUPABASE_SERVICE_ROLE_KEY=...
python backend/engine/verify_supabase.py
```

### Seed catalog (first-time)
```bash
python backend/engine/seed_supabase.py
```

### Run price worker locally (same as GitHub Actions)
```bash
python backend/worker.py
```

### Backfill YTD price history (LOCAL — uncommitted)
```bash
# Preview
python backend/engine/backfill_supabase.py --dry-run

# Insert ~3,400 daily snapshot rows (Mar 2026 → today) + optional historical alerts
python backend/engine/backfill_supabase.py --with-alerts

# Re-run safely
python backend/engine/backfill_supabase.py --force --with-alerts
```

**Note**: PriceToken history API (`GET /api/v1/text/history?days=150`) only goes back to ~**2026-03-04**, not Jan 1. See [`backend/engine/fetch_price_history.py`](backend/engine/fetch_price_history.py).

### Tests
```bash
pip install -r backend/requirements.txt
python -m pytest backend/tests/ -v
```

### Web dev
```bash
cd web && npm install && npm run dev
```

---

## YTD History (committed — operator steps remain)

| File | Purpose |
|------|---------|
| `backend/engine/fetch_price_history.py` | Fetches pricetoken.ai `/api/v1/text/history` |
| `backend/engine/backfill_supabase.py` | Bulk insert snapshots + generate historical drop alerts |
| `backend/engine/supabase_sync.py` | `bulk_insert_price_snapshots()` |
| `web/components/PriceSparkline.tsx` | SVG sparkline + period % badge |
| `supabase/migrations/002_snapshots_90day_free.sql` | Free tier: 90-day snapshot window (run in SQL editor) |

**Operator next steps**:
1. Apply `002_snapshots_90day_free.sql` in Supabase SQL editor
2. Run `python3 backend/engine/backfill_supabase.py --with-alerts` with prod env vars
3. Push to `main` and verify sparklines on Vercel
4. Optionally add one-time GitHub Actions workflow for backfill

---

## Environment Variables

### Vercel (`web/`)
```
NEXT_PUBLIC_SUPABASE_URL=https://eamkkmlpphsimvznjjcf.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...        # Stripe webhook
NEXT_PUBLIC_APP_URL=https://....vercel.app
STRIPE_SECRET_KEY=...                # when enabling payments
STRIPE_WEBHOOK_SECRET=...
STRIPE_PRICE_ID_PRO_MONTHLY=...
```

### GitHub Actions secrets
```
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
RESEND_API_KEY          # optional — premium alert emails
RESEND_FROM_EMAIL       # optional
SLACK_BOT_TOKEN         # optional
SLACK_CHANNEL_ID        # optional
```

See [`.env.example`](.env.example) for full list.

---

## Supabase Auth Checklist (already done by human)

- [x] Migration SQL applied
- [x] Email provider enabled
- [x] Custom SMTP via Resend
- [x] Redirect URLs: `{APP_URL}/auth/callback` (local + Vercel)
- [ ] Google OAuth (optional — button exists in `web/app/login/page.tsx`)

---

## Product UX Flow

1. **Landing** (`/`) — terminal boot animation
2. **Login** (`/login`) — magic link or Google
3. **Onboarding** (`/onboarding`) — pick watchlist items
4. **Feed** (`/feed`) — alerts + news (Realtime)
5. **Models** (`/models`) — catalog by provider
6. **Watchlist** (`/watchlist`) — tracked items
7. **Settings** (`/settings`) — subscription status
8. **Pricing** (`/pricing`) — Stripe Checkout ($19/mo premium)

Design tokens: [`packages/theme/tokens.ts`](packages/theme/tokens.ts)  
Design doc: [`docs/design-system.md`](docs/design-system.md)

---

## True Cost & Alerts (core IP)

- Formula: [`docs/true_cost_formula.md`](docs/true_cost_formula.md)
- Calculator: [`backend/engine/calculate_true_cost.py`](backend/engine/calculate_true_cost.py)
- Alert logic: [`backend/engine/validate_alerts.py`](backend/engine/validate_alerts.py)
- Orchestrator: [`backend/engine/run_price_hunter.py`](backend/engine/run_price_hunter.py)

**First worker run**: baselines = current prices → **0 alerts** (by design).  
**Demo alerts**: `python backend/engine/demo_price_alert.py`  
**Historical alerts**: `backfill_supabase.py --with-alerts`

---

## Known Issues & Gotchas

1. **Supabase URL must be API URL** (`https://REF.supabase.co`), not dashboard URL — `normalize_supabase_url()` handles this in `supabase_sync.py`.
2. **Table Editor**: data lives in `public.models`, not `auth.users` (empty until login).
3. **Built-in Supabase email rate limit** (~4/hr) — fixed via Resend SMTP; see [`docs/auth-email-resend.md`](docs/auth-email-resend.md).
4. **pricepertoken.com fallback API returns 404** — primary source is pricetoken.ai only.
5. **Free tier RLS**: authenticated users only see 7 days of `price_snapshots` unless premium — backfilled YTD data requires premium or policy adjustment for demo.
6. **`model_capabilities` in Supabase**: only 7 rows with full benchmarks; 41 models seeded but capabilities sparse for some.
7. **Savings projections** in routing config are illustrative, not tied to real usage.

---

## Priority Roadmap (recommended order)

### P0 — Complete YTD history feature (in progress)
- [x] Commit backfill scripts + sparkline UI
- [ ] Push to `main` / verify Vercel
- [ ] Run `backfill_supabase.py --with-alerts` on production Supabase
- [x] Price sparklines + period % badge on `/models` and `/watchlist`
- [x] RLS migration: 90-day window for free (`002_snapshots_90day_free.sql`)

### P1 — Monetization
- [ ] Stripe live mode: product, webhook, test checkout end-to-end
- [ ] Verify `subscriptions` table updates and premium gates unlock

### P2 — Feed content
- [ ] Confirm GitHub Actions cron populates `price_snapshots` daily
- [ ] Implement Routine 2 (`check_releases.py`) → `market_events` table
- [ ] Run `supabase/seed.sql` or expand news ingest

### P3 — Polish
- [ ] Custom Supabase email templates (Mr. Robot copy)
- [ ] Landing page copy + custom domain on Vercel
- [ ] Privacy policy / terms URLs (required for Stripe)

### P4 — iOS (post-revenue)
- [ ] See [`mobile/README.md`](mobile/README.md) and [`docs/app-store-checklist.md`](docs/app-store-checklist.md)

---

## Git History (pushed)

```
c85eadc Fix auth email rate limits with Resend SMTP guide and Google login fallback
7378668 Add web platform monorepo with Supabase backend and Vercel-ready Next.js app
8440452 Add Phase 1 MVP scaffold for AI Model Intelligence Platform
```

---

## Reference Docs

| Doc | Contents |
|-----|----------|
| [`CONTEXT_AI_MODEL_INTELLIGENCE_PLATFORM.md`](CONTEXT_AI_MODEL_INTELLIGENCE_PLATFORM.md) | Original product vision, 7 gaps, Routine specs |
| [`HANDOFF.md`](HANDOFF.md) | Phase 1 CLI-era handoff (partially superseded) |
| [`docs/deployment.md`](docs/deployment.md) | Vercel, Supabase, Stripe, GitHub Actions |
| [`docs/auth-email-resend.md`](docs/auth-email-resend.md) | Fix auth rate limits |
| [`README.md`](README.md) | Quick start |

---

## For the Next Agent

1. **Read this file first**, then `docs/deployment.md`.
2. **Do not rotate or log secrets** — ask the human to set env vars in Vercel/GitHub/Supabase dashboards.
3. **Commit the backfill work** before building UI sparklines — feed and models pages need `price_snapshots` populated.
4. **Test RLS as a free user** after backfill — 7-day window may hide YTD data; may need policy update.
5. **Run pytest** after backend changes; **run `npm run build`** in `web/` after frontend changes.
6. **Vercel root directory is `web`** — not repo root.

---

*Handoff prepared: May 31, 2026*
