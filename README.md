# Pricing Sentinel

Active intelligence platform — **which AI model to use, when, and why**. Mr. Robot terminal aesthetic. Web-first on Supabase + Vercel; iOS when revenue funds the Apple Developer account.

## Monorepo structure

```
pricing-sentinel/
├── web/              Next.js app → deploy to Vercel
├── backend/          Python engine + worker + tests
├── supabase/         Postgres migrations + seed
├── packages/theme/   Shared design tokens (web + future iOS)
├── mobile/           iOS placeholder (Phase 2)
└── docs/             Deployment + App Store checklists
```

## Quick start

### Backend (local)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
python -m pytest backend/tests/ -v
python backend/engine/fetch_prices.py
python backend/worker.py   # syncs to Supabase when env set
```

### Web (local)

```bash
cd web && cp .env.local.example .env.local
npm install && npm run dev
# → http://localhost:3000
```

### Production deploy

See [docs/deployment.md](docs/deployment.md) — Supabase + Vercel + Stripe + GitHub Actions cron.

## Product features

| Feature | Free | Premium ($19/mo) |
|---------|------|------------------|
| Model catalog | ✓ | ✓ |
| Watchlist | 3 items | Unlimited |
| Price alerts | 24h delay | Realtime |
| Price history | 90 days | Full |
| TERMINAL + DESK | ✓ | ✓ |
| Email alerts | — | ✓ |
| AI news feed | Teaser | Full |

## Core engine

- **True Cost** formula: [`docs/true_cost_formula.md`](docs/true_cost_formula.md)
- **Price hunter**: [`backend/engine/run_price_hunter.py`](backend/engine/run_price_hunter.py)
- **FastAPI** (dev only): `uvicorn backend.api.main:app --reload`

## Handoff docs

- [CODING_SESSION_HANDOFF.md](CODING_SESSION_HANDOFF.md) — **start here** for next coding session
- [CONTEXT_AI_MODEL_INTELLIGENCE_PLATFORM.md](CONTEXT_AI_MODEL_INTELLIGENCE_PLATFORM.md) — product vision
- [docs/LAUNCH.md](docs/LAUNCH.md) — deploy, Stripe, cron secrets
