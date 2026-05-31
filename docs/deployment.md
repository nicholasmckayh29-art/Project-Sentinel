# Deployment Guide

## Stack (free tier)

| Service | Role |
|---------|------|
| [Supabase](https://supabase.com) | Postgres, Auth, Realtime |
| [Vercel](https://vercel.com) | Next.js web app |
| [GitHub Actions](https://github.com) | Daily price sync cron |
| [Stripe](https://stripe.com) | Web subscriptions |
| [Resend](https://resend.com) | Premium email alerts (100/day free) |

## 1. Supabase setup

1. Create a project at supabase.com
2. Run SQL from [`supabase/migrations/001_initial_schema.sql`](../supabase/migrations/001_initial_schema.sql) in the SQL editor
3. Enable Email auth (Authentication → Providers)
4. Copy **Project URL** (format: `https://YOUR-REF.supabase.co`) — **not** the dashboard browser URL

Seed catalog from local JSON:

```bash
export SUPABASE_URL=...
export SUPABASE_SERVICE_ROLE_KEY=...
python backend/engine/seed_supabase.py
```

## 2. Vercel deploy

1. Import repo on vercel.com
2. Set **Root Directory** to `web`
3. Add environment variables from `.env.example`
4. Deploy

## 3. Stripe setup

1. Create product "Pricing Sentinel Pro" — $19/mo recurring
2. Copy Price ID → `STRIPE_PRICE_ID_PRO_MONTHLY`
3. Add webhook endpoint: `https://your-app.vercel.app/api/stripe/webhook`
4. Events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`
5. Copy webhook secret → `STRIPE_WEBHOOK_SECRET`

## 4. GitHub Actions cron

Add repository secrets:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `RESEND_API_KEY` (optional)
- `RESEND_FROM_EMAIL` (optional)

Workflow: [`.github/workflows/price-sync.yml`](../.github/workflows/price-sync.yml) — weekdays 9am UTC.

Manual run: Actions → Price Sync Worker → Run workflow.

## 5. Local development

```bash
# Backend tests
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
python -m pytest backend/tests/ -v

# Web app
cd web && cp .env.local.example .env.local
npm install && npm run dev
```

## 6. iOS (Phase 2)

See [`mobile/README.md`](../mobile/README.md) — fund Apple Developer account from web revenue first.
