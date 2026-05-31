# Pricing Sentinel — Coding Session Handoff

> **Date**: May 31, 2026  
> **Repo**: `/Users/nich/Projects/pricing-sentinel`  
> **GitHub**: [nicholasmckayh29-art/Project-Sentinel](https://github.com/nicholasmckayh29-art/Project-Sentinel)  
> **Branch**: `main`  
> **Latest commit**: `6d02399` — Market terminal, DESK, ingest pipeline  
> **Vercel**: Root directory = `web` (auto-deploy from `main`)

---

## Executive summary

Pricing Sentinel is an **AI model decision layer** (True Cost, alerts, routing) with a **Bloomberg-style terminal UI** (Mr. Robot palette). The May 31 session shipped **TERMINAL** (`/feed`), **DESK** (`/desk`), multi-source news/equity ingest, and migrations `003`–`006`.

**Human operator completed today:**
- Supabase migrations `003`–`006` applied
- Manual SQL fix: `market_events.url_hash` **UNIQUE constraint** (see Known issues)
- `pip install -r backend/requirements.txt` in `.venv`
- `python backend/market_sync_worker.py` — **working** (~100 events, 6 equity quotes)
- Push to `main` → Vercel redeploy triggered

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
| Auth (magic link + Google) | ✅ |
| **TERMINAL** `/feed` — ticker, price tape, news wire, sentiment, macro bar | ✅ UI + data after market sync |
| **DESK** `/desk` — ModelPicker, line/bar/table, research wire, community pulse, route panel | ✅ Partial (see bugs) |
| Model catalog `/models` → links to DESK | ✅ |
| Watchlist models — DB CRUD | ✅ |
| News ingest (HN, RSS, arXiv, OpenAlex, GitHub, etc.) | ✅ |
| Equity quotes (yfinance dev / Finnhub prod) | ✅ |
| Price backfill + sparklines | ✅ Scripts exist; run if charts empty |
| Routing recommendations table + weekly sync | ✅ Code; needs `routing_sync_worker` run |
| Stripe live / premium gates | ⚠️ Code exists; not fully wired in prod |
| GitHub Actions secrets for market sync | ⚠️ Add `FINNHUB_API_KEY`, optional `FRED_API_KEY`, etc. |

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

## Key files (start here tomorrow)

| Path | Purpose |
|------|---------|
| [`web/components/terminal/TerminalLayout.tsx`](web/components/terminal/TerminalLayout.tsx) | TERMINAL orchestrator + Realtime |
| [`web/components/terminal/DeskClient.tsx`](web/components/terminal/DeskClient.tsx) | DESK panel grid |
| [`web/components/terminal/ModelPicker.tsx`](web/components/terminal/ModelPicker.tsx) | DESK model chips (needs clear-all) |
| [`web/components/WatchlistManager.tsx`](web/components/WatchlistManager.tsx) | Watchlist UI (providers/workloads not wired to feed) |
| [`web/components/terminal/charts/PieCostPanel.tsx`](web/components/terminal/charts/PieCostPanel.tsx) | Broken pie chart |
| [`web/app/(dashboard)/feed/page.tsx`](web/app/(dashboard)/feed/page.tsx) | TERMINAL server data |
| [`web/app/(dashboard)/desk/page.tsx`](web/app/(dashboard)/desk/page.tsx) | DESK server data |
| [`web/lib/terminal-data.ts`](web/lib/terminal-data.ts) | Watchlist-scoped alerts/ticker helpers |
| [`backend/engine/ingest_news.py`](backend/engine/ingest_news.py) | All news sources |
| [`backend/engine/supabase_sync.py`](backend/engine/supabase_sync.py) | DB sync helpers |
| [`backend/market_sync_worker.py`](backend/market_sync_worker.py) | News + quotes + macro + community |
| [`supabase/migrations/003_market_quotes.sql`](supabase/migrations/003_market_quotes.sql) | Quotes + url_hash constraint |

**Docs**: [`docs/LAUNCH.md`](docs/LAUNCH.md) · [`docs/future-projections.md`](docs/future-projections.md) · [`docs/future-quantum.md`](docs/future-quantum.md)

---

## Known bugs (fix first tomorrow)

### 1. DESK ModelPicker — no “clear all”

**Symptom**: User must click each selected model chip to deselect; no one-click clear.

**Where**: [`ModelPicker.tsx`](web/components/terminal/ModelPicker.tsx) — only per-chip toggle; when deselecting last chip, URL param `models` is removed but no explicit “Clear selection” control.

**Fix**: Add a **CLEAR ALL** button that sets `selected` to `[]` and navigates to `/desk` without `?models=`. Respect free-tier UX (empty state → show watchlist CTA).

---

### 2. Watchlist providers & workload presets do nothing for TERMINAL/DESK

**Symptom**: User selects providers/workloads on `/watchlist`; TERMINAL and DESK behave as if only **model** watchlist matters.

**Root cause**:
- [`feed/page.tsx`](web/app/(dashboard)/feed/page.tsx) and [`desk/page.tsx`](web/app/(dashboard)/desk/page.tsx) only query `user_watchlist_models`.
- [`WatchlistManager.tsx`](web/components/WatchlistManager.tsx) copy says “Alerts filter to your selections” but providers/workloads are stored in DB and **never read** by feed/desk queries.
- `watchlist_count()` RLS counts all three types toward the 3-item free cap, but filtering logic ignores providers/workloads.

**Fix options** (pick one product shape):
- **A)** When provider watched → include all models for that provider in ticker/DESK picker and alert filter.
- **B)** When workload watched → filter alerts by `workload_id`, show True Cost on DESK for that workload, drive RoutePanel from watched workloads only.
- **C)** Update watchlist copy to “Models only affect TERMINAL/DESK today” until wired.

**Files to touch**: `terminal-data.ts`, `feed/page.tsx`, `desk/page.tsx`, possibly `WatchlistManager` empty states.

---

### 3. Pie chart — invisible labels + chart not rendering

**Symptom**: DESK pie/donut has dark labels on black background; chart appears broken.

**Where**: [`PieCostPanel.tsx`](web/components/terminal/charts/PieCostPanel.tsx)

**Likely causes**:
1. **Data source**: Pie uses `models.pricing` from catalog (`DeskClient` passes `primary?.pricing?.input_per_1m`) — not latest `price_snapshots`. If catalog JSON empty/malformed → shows “NO PRICING DATA” or zero slices.
2. **Recharts + dark theme**: No `Legend`/`Label` styling; default text may be `#000`. Need explicit `fill="#e0e0e0"` on labels/legend or custom `label` renderer with terminal colors.
3. **ResponsiveContainer**: Known SSR/hydration issue in flex layouts — chart area can render at 0×0. Try fixed `height={200}` or `minHeight` on parent.

**Fix**:
- Prefer **latest snapshot** for pie (same as line chart): pass `input_per_1m` / `output_per_1m` from last row in `tableRows` for primary model.
- Add `Legend` with `wrapperStyle={{ color: '#888' }}` or use center label with `$X in / $Y out` text.
- Add `LabelList` with light fill or tooltip-only + summary stats below chart.

---

### 4. Ingest warnings (non-blocking)

| Warning | Notes |
|---------|--------|
| pricetoken release feed 404 | [`check_releases.py`](backend/engine/check_releases.py) — feed URL dead; other sources OK |
| Bluesky 403 | Optional; consider removing or retry with auth |
| `FRED_API_KEY` unset | Macro bar empty until key added |

---

### 5. Migration `url_hash` (fixed in prod manually)

Repo migration [`003_market_quotes.sql`](supabase/migrations/003_market_quotes.sql) now uses `UNIQUE (url_hash)` constraint (PostgREST-compatible). If any env still has partial index only, run:

```sql
DROP INDEX IF EXISTS idx_market_events_url_hash;
ALTER TABLE market_events DROP CONSTRAINT IF EXISTS market_events_url_hash_key;
ALTER TABLE market_events ADD CONSTRAINT market_events_url_hash_key UNIQUE (url_hash);
```

---

## Remaining work — full vision

### Phase 1 polish (short)

- [ ] Fix bugs above (clear-all, watchlist wiring, pie chart)
- [ ] Run `python backend/engine/backfill_supabase.py --with-alerts` if DESK charts empty
- [ ] Run `python backend/routing_sync_worker.py` once to populate DESK route panel
- [ ] Add GitHub secrets for `news-sync.yml` (`FINNHUB_API_KEY`, optional `FRED_API_KEY`)
- [ ] Update [`README.md`](README.md) product table (90-day free history, TERMINAL/DESK)

### Phase 1.5 — enrichment backlog

- [ ] Hashnode, Reddit ingest (env-gated)
- [ ] Research wire tagged to **watched model keywords** (not global arXiv dump)
- [ ] FRED macro bar populated in prod
- [ ] Provider logos on `/models` catalog rows (Clearbit already in ModelPicker)
- [ ] MarketAux ticker-tagged news (needs `MARKETAUX_API_KEY`)
- [ ] WSB retail sentiment weight in SentimentPanel

### Phase 2 — intelligence

- [ ] Richer alert cards in price tape (compact format + leader fields everywhere)
- [ ] DESK route panel filtered by **watched workloads**
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
| `/feed` | `TerminalLayout` | alerts, market_events, market_quotes, macro, community, watchlist models |
| `/desk` | `DeskClient` | snapshots, models, alerts, research events, routing_recommendations |
| `/watchlist` | `WatchlistManager` | user_watchlist_* |
| `/models` | catalog + sparklines | price_snapshots |

Nav: **TERMINAL** · **DESK** · **MODELS** · **WATCHLIST** · **SETTINGS**

---

## Tests

```bash
python -m pytest backend/tests/ -v   # 38 passing (May 31)
cd web && npm run build              # must pass before deploy
```

---

## Deleted / cleaned this session

| Removed | Why |
|---------|-----|
| `web/components/IntelFeed.tsx` | Replaced by `TerminalLayout` |
| `HANDOFF.md` | Obsolete Phase 1 CLI handoff |
| `AGENT_HANDOFF.md` | Superseded by this file |
| `data/market_events.json` | Local stub; ingest writes to Supabase |
| `config/cron_schedules.yaml` | Pointed at non-existent `scripts/`; use `.github/workflows/` |

---

## Suggested tomorrow session order

1. **Pie chart fix** (quick visual win on DESK)  
2. **ModelPicker clear-all** (UX)  
3. **Wire provider/workload watchlist** to feed filter + DESK route panel  
4. **Backfill + routing sync** if data still thin  
5. **Stripe / GitHub secrets** if time  

Good luck — the terminal skeleton is live; tomorrow is wiring watchlist semantics and DESK polish.
