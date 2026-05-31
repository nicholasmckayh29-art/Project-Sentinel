# Pricing Sentinel — Coding Session Handoff

> **Last updated**: May 31, 2026  
> **Repo**: `/Users/nich/Projects/pricing-sentinel`  
> **GitHub**: [nicholasmckayh29-art/Project-Sentinel](https://github.com/nicholasmckayh29-art/Project-Sentinel)  
> **Branch**: `main`  
> **Latest commit**: `8144638` — Tagline + site credits  
> **Prior commit**: `76d8764` — DESK bug fixes, watchlist scope wiring  
> **Vercel**: Root directory = `web` (auto-deploy from `main`)

---

## Executive summary

Pricing Sentinel is an **AI model decision layer** (True Cost, alerts, routing) with a **Bloomberg-style terminal UI** (Mr. Robot palette). TERMINAL (`/feed`) and DESK (`/desk`) are live with multi-source ingest, migrations `003`–`006`, and watchlist-aware filtering.

**Phase 1 polish bugs are fixed** in `76d8764` (pie chart, ModelPicker clear-all, provider/workload watchlist wiring). README product table is updated.

**Next up**: commit local Google OAuth redirect fixes, add GitHub Action secrets, run backfill/routing sync if data is thin, then Phase 1.5 enrichment.

**North star doc**: [`CONTEXT_AI_MODEL_INTELLIGENCE_PLATFORM.md`](CONTEXT_AI_MODEL_INTELLIGENCE_PLATFORM.md)

---

## Live infrastructure

| Service | Detail |
|---------|--------|
| Supabase | `eamkkmlpphsimvznjjcf` · `https://eamkkmlpphsimvznjjcf.supabase.co` |
| GitHub Actions | `price-sync.yml` (weekdays 9:00 UTC), `news-sync.yml` (every 6h), `routing-sync.yml` (Mon 10:00 UTC) |
| Local workers | `backend/worker.py`, `backend/market_sync_worker.py`, `backend/routing_sync_worker.py` |

**Never commit**: `.env`, `web/.env.local`, service role keys, Stripe/Resend secrets.

---

## What works today

| Area | Status |
|------|--------|
| Auth (magic link + Google) | ✅ Code on main; OAuth redirect hardening **uncommitted** (see below) |
| **TERMINAL** `/feed` — ticker, price tape, news wire, sentiment, macro bar | ✅ Watchlist-scoped alerts + ticker |
| **DESK** `/desk` — ModelPicker, charts, research wire, community pulse, route panel | ✅ Pie chart, clear-all, provider models in picker |
| Watchlist — models, providers, workloads | ✅ All three affect TERMINAL/DESK (see semantics below) |
| Model catalog `/models` → links to DESK | ✅ |
| News ingest (HN, RSS, arXiv, OpenAlex, GitHub, etc.) | ✅ |
| Equity quotes (yfinance dev / Finnhub prod) | ✅ |
| Price backfill + sparklines | ✅ Scripts exist; run if charts empty |
| Routing recommendations + weekly sync | ✅ Code; run `routing_sync_worker` to populate route panel |
| Stripe live / premium gates | ⚠️ Code exists; not fully wired in prod |
| GitHub Actions secrets for market sync | ⚠️ Add `FINNHUB_API_KEY`, optional `FRED_API_KEY` |

---

## Watchlist semantics (implemented)

| Watchlist type | TERMINAL `/feed` | DESK `/desk` |
|----------------|------------------|--------------|
| **Models** | Ticker + alert filter | ModelPicker chips, charts, alerts |
| **Providers** | All models for provider merged into ticker + alert filter | Provider models appear in ModelPicker |
| **Workloads** | Alerts filtered by `workload_id` | Route panel filtered to watched workloads only |

**Helpers**: [`web/lib/terminal-data.ts`](web/lib/terminal-data.ts) — `mergeModelIds`, `filterAlertsByScope`, `buildModelTicks`.

**Partial gaps**:
- DESK **alerts** filter by selected **models** only (not workload-scoped).
- DESK **research wire** is still a global arXiv/release dump (Phase 1.5).

---

## Architecture

```
External APIs (HN, RSS, arXiv, yfinance/Finnhub, …)
       ↓
backend/market_sync_worker.py  — manual or news-sync.yml every 6h
backend/worker.py              — price-sync.yml weekdays
       ↓
Supabase (market_events, market_quotes, price_snapshots, alerts, …)
       ↓
Next.js on Vercel (anon key + RLS)
       ↓
/feed (TerminalLayout) · /desk (DeskClient) · /watchlist · /models
```

---

## Key files (start here)

| Path | Purpose |
|------|---------|
| [`web/components/terminal/TerminalLayout.tsx`](web/components/terminal/TerminalLayout.tsx) | TERMINAL orchestrator + Realtime |
| [`web/components/terminal/DeskClient.tsx`](web/components/terminal/DeskClient.tsx) | DESK panel grid; passes snapshot pricing to pie |
| [`web/components/terminal/ModelPicker.tsx`](web/components/terminal/ModelPicker.tsx) | DESK model chips + CLEAR ALL |
| [`web/components/terminal/charts/PieCostPanel.tsx`](web/components/terminal/charts/PieCostPanel.tsx) | Input/output cost donut (dark-theme legend) |
| [`web/app/(dashboard)/feed/page.tsx`](web/app/(dashboard)/feed/page.tsx) | TERMINAL server data + watchlist scope |
| [`web/app/(dashboard)/desk/page.tsx`](web/app/(dashboard)/desk/page.tsx) | DESK server data + provider/workload scope |
| [`web/lib/terminal-data.ts`](web/lib/terminal-data.ts) | Watchlist-scoped alerts/ticker helpers |
| [`web/lib/auth-url.ts`](web/lib/auth-url.ts) | OAuth redirect origin helper (**uncommitted**) |
| [`backend/engine/ingest_news.py`](backend/engine/ingest_news.py) | All news sources |
| [`backend/market_sync_worker.py`](backend/market_sync_worker.py) | News + quotes + macro + community |

**Docs**: [`docs/LAUNCH.md`](docs/LAUNCH.md) · [`docs/google-oauth-setup.md`](docs/google-oauth-setup.md) (**uncommitted**) · [`docs/future-projections.md`](docs/future-projections.md)

---

## Recently fixed (`76d8764`)

### 1. DESK ModelPicker — CLEAR ALL ✅

[`ModelPicker.tsx`](web/components/terminal/ModelPicker.tsx): `clearAll()` removes `?models=` and navigates to `/desk`.

### 2. Watchlist providers & workloads wired ✅

- **Providers** → all models for that provider merged via `mergeModelIds` on feed + desk.
- **Workloads** → `filterAlertsByScope` on TERMINAL; route panel filtered on DESK.

### 3. Pie chart ✅

[`PieCostPanel.tsx`](web/components/terminal/charts/PieCostPanel.tsx): styled legend/tooltip, `min-h-[140px]`, summary stats. [`DeskClient.tsx`](web/components/terminal/DeskClient.tsx) uses latest snapshot row for primary model.

### 4. Release feed URL ✅

[`check_releases.py`](backend/engine/check_releases.py): switched to `pricepertoken.com/feed` with graceful fallback.

### 5. README product table ✅

90-day free history, TERMINAL + DESK rows added.

---

## Uncommitted work (commit first)

Local changes not yet on `main`:

| File | Change |
|------|--------|
| [`docs/google-oauth-setup.md`](docs/google-oauth-setup.md) | New — Google Cloud + Supabase + Vercel redirect checklist |
| [`web/lib/auth-url.ts`](web/lib/auth-url.ts) | New — `getRedirectOrigin()` for prod/preview |
| [`web/app/auth/callback/route.ts`](web/app/auth/callback/route.ts) | OAuth error handling + redirect origin |
| [`web/app/login/page.tsx`](web/app/login/page.tsx) | Google sign-in redirect fixes |
| [`web/lib/supabase/middleware.ts`](web/lib/supabase/middleware.ts) | Minor session tweak |
| [`docs/auth-email-resend.md`](docs/auth-email-resend.md) | Resend SMTP notes |
| [`docs/deployment.md`](docs/deployment.md) | Trimmed; OAuth details moved to google-oauth-setup |

**Suggested commit message**: `Fix Google OAuth redirects and add setup guide`

---

## Known gaps (non-blocking)

| Item | Notes |
|------|--------|
| Bluesky 403 | Optional ingest source in `ingest_news.py`; safe to ignore or remove |
| `FRED_API_KEY` unset | Macro bar empty until key added to env + GitHub secrets |
| `market_events.url_hash` | Fixed in prod manually; migration `003` has correct `UNIQUE` constraint |
| DESK research wire | Global feed — not yet tagged to watched model keywords |

If any env still has partial index only on `url_hash`:

```sql
DROP INDEX IF EXISTS idx_market_events_url_hash;
ALTER TABLE market_events DROP CONSTRAINT IF EXISTS market_events_url_hash_key;
ALTER TABLE market_events ADD CONSTRAINT market_events_url_hash_key UNIQUE (url_hash);
```

---

## Remaining work — full vision

### Immediate (this session)

- [ ] Commit Google OAuth redirect fixes + `docs/google-oauth-setup.md`
- [ ] Run `python backend/engine/backfill_supabase.py --with-alerts` if DESK charts empty
- [ ] Run `python backend/routing_sync_worker.py` once to populate DESK route panel
- [ ] Add GitHub secrets for `news-sync.yml` (`FINNHUB_API_KEY`, optional `FRED_API_KEY`)

### Phase 1.5 — enrichment backlog

- [ ] Hashnode, Reddit ingest (env-gated)
- [ ] Research wire tagged to **watched model keywords** (not global arXiv dump)
- [ ] FRED macro bar populated in prod
- [ ] Provider logos on `/models` catalog rows (Clearbit already in ModelPicker)
- [ ] MarketAux ticker-tagged news (needs `MARKETAUX_API_KEY`)
- [ ] WSB retail sentiment weight in SentimentPanel
- [ ] DESK alerts scoped by watched workloads (TERMINAL already does)

### Phase 2 — intelligence

- [ ] Richer alert cards in price tape (compact format + leader fields everywhere)
- [ ] Cron: ensure `routing-sync.yml` runs after price sync with fresh `current_prices.json`
- [ ] Wire alert `action` line from price hunter metadata consistently

### Phase 3 — launch

- [ ] Stripe live mode ([`docs/LAUNCH.md`](docs/LAUNCH.md))
- [ ] Premium Realtime verified end-to-end on prod
- [ ] Landing: optional live terminal embed (static preview exists on `/`)
- [ ] Email/Slack digest with QuickChart (code started in `email_digest.py`, `slack_formatter.py`)

### Stretch (documented, not started)

- Provider status lane, CoinGecko strip, Monte Carlo bands ([`docs/future-projections.md`](docs/future-projections.md)), IBM Quantum ([`docs/future-quantum.md`](docs/future-quantum.md))

---

## Operator commands (copy-paste)

```bash
cd /Users/nich/Projects/pricing-sentinel
source .venv/bin/activate
export SUPABASE_URL="https://eamkkmlpphsimvznjjcf.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="..."

# Price history + alerts for charts
python backend/engine/backfill_supabase.py --with-alerts

# News, equities, community signals
python backend/market_sync_worker.py

# Routing recommendations for DESK
python backend/engine/fetch_prices.py
python backend/routing_sync_worker.py

# Daily price sync (also via GitHub Actions)
python backend/worker.py
```

**Vercel env** (web): `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_APP_URL`, Stripe vars when ready.

---

## Routes map

| Route | Component | Data |
|-------|-----------|------|
| `/feed` | `TerminalLayout` | alerts (watchlist-scoped), market_events, market_quotes, macro, community, effective model ticks |
| `/desk` | `DeskClient` | snapshots, models, alerts, research events, routing_recommendations (workload-filtered) |
| `/watchlist` | `WatchlistManager` | user_watchlist_models / providers / workloads |
| `/models` | catalog + sparklines | price_snapshots |

Nav: **TERMINAL** · **DESK** · **MODELS** · **WATCHLIST** · **SETTINGS**

---

## Tests

```bash
python -m pytest backend/tests/ -v   # 38 passing (May 31)
cd web && npm run build              # must pass before deploy
```

---

## Suggested next session order

1. **Commit OAuth fixes** — uncommitted auth-url + callback + google-oauth-setup doc  
2. **Verify Google sign-in on prod** — follow [`docs/google-oauth-setup.md`](docs/google-oauth-setup.md)  
3. **Backfill + routing sync** if DESK charts or route panel are empty  
4. **GitHub secrets** — `FINNHUB_API_KEY`, `FRED_API_KEY`  
5. **Phase 1.5** — research wire scoped to watchlist, provider logos on `/models`  
6. **Stripe** when ready for launch  

Terminal + DESK are feature-complete for Phase 1; focus shifts to auth hardening in prod, data freshness, and enrichment.
