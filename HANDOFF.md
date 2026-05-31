# AI Model Intelligence Platform — Implementation Handoff

> **Date**: May 31, 2026  
> **Repo**: `/Users/nich/Projects/pricing-sentinel`  
> **Branch**: `cursor/phase-1-mvp-scaffold`  
> **Latest commit**: `8440452` — *Add Phase 1 MVP scaffold for AI Model Intelligence Platform.*  
> **Status**: Phase 1 CLI prototype — real data, real math, no HTTP API or frontend yet

---

## Executive Summary

This project implements the **decision layer** for AI model pricing: not another dashboard, but automated judgment about **which model to use, when, and why**.

What exists today is a **working backend brain** implemented as Python CLI scripts with JSON file storage. It fetches live pricing, computes workload-aware True Cost, validates alerts, and generates routing recommendations. It does **not** yet expose an HTTP API, UI, database, or live Slack/email delivery.

---

## What Was Built (Completed)

### Repository & Git

| Item | Detail |
|------|--------|
| Location | `/Users/nich/Projects/pricing-sentinel` |
| Branch | `cursor/phase-1-mvp-scaffold` (not pushed) |
| Commits | 1 root commit, 24 files |
| Spec doc | `CONTEXT_AI_MODEL_INTELLIGENCE_PLATFORM.md` (condensed product handoff) |

### Core Scripts (`scripts/`)

| Script | Purpose | Status |
|--------|---------|--------|
| `fetch_prices.py` | Fetches live model pricing, writes `data/current_prices.json` | ✅ Verified (41 models) |
| `calculate_true_cost.py` | True Cost + Value Score + quality gate logic | ✅ Unit tested |
| `validate_alerts.py` | 15%/25% drop detection, new-model entry logic | ✅ Unit tested |
| `run_price_hunter.py` | Routine 1 orchestrator: fetch → baseline → alert → history | ✅ End-to-end verified |
| `check_releases.py` | Routine 2 stub: scans release feed → `market_events.json` | ⚠️ Stub (feed may 404) |
| `generate_routing_config.py` | Routine 3: workload routing + savings projection | ✅ Generates YAML |

### Alert Formatters (`alerts/`)

| Module | Purpose | Status |
|--------|---------|--------|
| `slack_formatter.py` | Slack Block Kit templates for price alerts | ✅ Built, not wired to Slack API |
| `email_digest.py` | HTML weekly briefing template | ✅ Built, not wired to Resend |

### Data Layer (`data/`)

| File | Role |
|------|------|
| `current_prices.json` | Live snapshot from pricetoken.ai (41 active models) |
| `baselines.json` | Historical price snapshots for alert comparison |
| `workloads.json` | 3 standard workloads (coding, bulk, customer support) |
| `model_capabilities.json` | Benchmark + efficiency overrides for key models |
| `market_events.json` | Seed market event + release feed output |
| `alert_history.json` | Append-only alert log |

### Configuration (`config/`)

| File | Role |
|------|------|
| `threshold_rules.json` | Alert thresholds (15% drop, 5% quality floor, 1.2× value multiplier) |
| `cron_schedules.yaml` | Cron specs for all 3 Cursor Routines |

### Documentation & Tests

| File | Role |
|------|------|
| `docs/true_cost_formula.md` | Transparent True Cost documentation |
| `tests/test_true_cost.py` | 6 passing tests (cost, value score, alert logic) |
| `README.md` | Quick start and project overview |

---

## Architecture (Current)

```
External APIs                    CLI Scripts                    Output
─────────────                    ───────────                    ──────
pricetoken.ai/api/v1/text  ──►  fetch_prices.py         ──►  current_prices.json
(pricepertoken fallback)         run_price_hunter.py     ──►  baselines.json
                                 validate_alerts.py      ──►  alert_history.json
                                 generate_routing_config ──►  routing_config.yaml
model_capabilities.json   ──►  calculate_true_cost.py
workloads.json
threshold_rules.json
```

**Not in architecture yet:** HTTP server, frontend, SQLite/Postgres, Slack/Resend connectors, Cursor Automations.

---

## How to Run & Test

```bash
cd /Users/nich/Projects/pricing-sentinel
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 1. Fetch live prices
python scripts/fetch_prices.py
# → {"status": "ok", "model_count": 41}

# 2. Run Price Drop Hunter (Routine 1)
python scripts/run_price_hunter.py
# → JSON with alert_count (0 on first run is expected)

# 3. Generate routing config (Routine 3)
python scripts/generate_routing_config.py
# → routing_config.yaml

# 4. Run tests
python -m pytest tests/ -v
# → 6 passed
```

### Sample Routing Output (last verified run)

```yaml
routes:
  - name: AI Coding Assistant
    workload_id: coding_assistant
    models:
      - model: deepseek-chat
        weight: 0.6
      - model: gpt-4o-mini
        weight: 0.4
    caching: true
    max_retries: 2
projections:
  current_monthly_spend_usd: 708.75
  optimized_monthly_spend_usd: 22.05
  projected_savings_usd: 686.7
  projected_savings_pct: 96.89
```

### Testing Alerts Manually

First run sets baselines equal to current prices → **no alerts fire**. To test alert logic:

1. Edit `data/baselines.json` — inflate `pricing.output_per_1m` for a tracked model (e.g. 2× current), or
2. Wait for a real price change from the API, or
3. Run `python -m pytest tests/test_true_cost.py` (covers alert trigger logic directly)

---

## Data Sources

| Priority | Source | Endpoint | Notes |
|----------|--------|----------|-------|
| Primary | [PriceToken](https://pricetoken.ai) | `GET /api/v1/text` | ✅ Working, 41+ active models |
| Fallback | [Price Per Token](https://pricepertoken.com) | `GET /api/v1/models` | ⚠️ Returns 404 as of May 2026 |
| Benchmarks | Local | `data/model_capabilities.json` | Curated for ~9 key models |
| Release feed | Price Per Token | `GET /feed` | ⚠️ Unverified in production |

---

## True Cost Formula (Implemented)

```
TrueCost = (output_per_1m × amplification × retry_mult × cache_mult × batch_disc) / 1000
```

| Variable | Implementation |
|----------|----------------|
| `amplification` | `(avg_output_tokens / 1000) × efficiency_ratio` |
| `retry_mult` | `1 + retry_rate` |
| `cache_mult` | `1 - cache_hit_rate` when caching supported + eligible |
| `batch_disc` | `0.8` when batch API + workload allows batching |

See `docs/true_cost_formula.md` and `scripts/calculate_true_cost.py`.

---

## Cursor Routines (Specified, Not Wired)

| Routine | Cron | Script | Wired? |
|---------|------|--------|--------|
| 1 — Price Drop Hunter | `0 9 * * 1-5` | `run_price_hunter.py` | ❌ Not created in Cursor Automations |
| 2 — Release Radar | `0 12 * * 1,4` | `check_releases.py` | ❌ |
| 3 — Stack Optimizer | `0 18 * * 5` | `generate_routing_config.py` | ❌ |

**Secrets needed when wiring:** `SLACK_BOT_TOKEN`, `RESEND_API_KEY` (optional)

Cron specs live in `config/cron_schedules.yaml`. Full Routine system prompts are in the original user handoff (see conversation context / expand `CONTEXT_AI_MODEL_INTELLIGENCE_PLATFORM.md`).

---

## What Is NOT Done Yet

### Phase 1 gaps (from README checklist)

- [ ] Cursor Routine 1 automation with Slack connector
- [ ] Baseline drift detection over time (revert-within-48h → `cyclical` tag)
- [ ] Live Slack message delivery (formatter exists, no API call)
- [ ] Live email delivery via Resend

### Original roadmap (not started)

- [ ] HTTP API (FastAPI: `/v1/alerts`, `/v1/routing`, `/v1/models`)
- [ ] Frontend / dashboard
- [ ] SQLite → PostgreSQL time-series storage
- [ ] Fly.io deployment
- [ ] GitHub remote (`my-org/pricing-sentinel`)
- [ ] Routine 2 full implementation (rumor scoring, Twitter/X, provider changelogs)
- [ ] Memory integration (Cursor Automations memory for rumor accuracy, alert history)
- [ ] `usage_mock.csv` / real spend ingestion for Stack Optimizer

---

## Known Issues & Limitations

1. **No HTTP backend** — scripts only; cannot connect a frontend without a FastAPI wrapper.
2. **JSON file storage** — not concurrent-safe; no history beyond baselines snapshot.
3. **Sparse benchmarks** — only ~9 models have benchmark overrides; bulk/support workloads may fail quality gates and get no route.
4. **Savings projections are illustrative** — Stack Optimizer compares cheapest eligible vs most expensive eligible; not tied to real usage.
5. **pricepertoken.com API fallback is broken** (404); primary source is pricetoken.ai only today.
6. **`routing_config.yaml` is gitignored** — generated locally, not committed.
7. **First-run alert silence** — by design; baselines initialize at current prices.

---

## File Inventory (Committed)

```
pricing-sentinel/
├── .gitignore
├── CONTEXT_AI_MODEL_INTELLIGENCE_PLATFORM.md
├── README.md
├── requirements.txt          # requests, pyyaml, pytest
├── alerts/
│   ├── __init__.py
│   ├── email_digest.py
│   └── slack_formatter.py
├── config/
│   ├── cron_schedules.yaml
│   └── threshold_rules.json
├── data/
│   ├── alert_history.json
│   ├── baselines.json
│   ├── current_prices.json
│   ├── market_events.json
│   ├── model_capabilities.json
│   └── workloads.json
├── docs/
│   └── true_cost_formula.md
├── scripts/
│   ├── __init__.py
│   ├── calculate_true_cost.py
│   ├── check_releases.py
│   ├── fetch_prices.py
│   ├── generate_routing_config.py
│   ├── run_price_hunter.py
│   └── validate_alerts.py
└── tests/
    └── test_true_cost.py
```

**Local only (gitignored):** `.venv/`, `routing_config.yaml`, `__pycache__/`, `.pytest_cache/`

---

## Recommended Next Steps (Priority Order)

1. **FastAPI wrapper** — expose `GET /api/models`, `/api/alerts`, `/api/routing`, `POST /api/refresh` so a frontend can connect.
2. **Wire Routine 1 in Cursor Automations** — cron + Slack connector posting formatted blocks from `run_price_hunter.py` output.
3. **Expand `model_capabilities.json`** — add benchmarks for all models returned by fetch, so all 3 workloads get routes.
4. **Push to GitHub** — create `my-org/pricing-sentinel` remote, open PR from `cursor/phase-1-mvp-scaffold`.
5. **Alert demo path** — script or test fixture that simulates a price drop against baselines for demo purposes.
6. **SQLite history** — store daily price snapshots for trend charts and cyclical detection.

---

## Dependencies

```
requests>=2.31.0
pyyaml>=6.0
pytest>=8.0
```

Python 3.9+ verified. No FastAPI, no database drivers yet.

---

## For the Next Agent

- **Product vision & full Routine prompts**: see original handoff in chat history or extend `CONTEXT_AI_MODEL_INTELLIGENCE_PLATFORM.md`.
- **Implementation status**: this file (`HANDOFF.md`).
- **Run commands**: `README.md`.
- **Math reference**: `docs/true_cost_formula.md`.
- **Entry point for Routine 1**: `scripts/run_price_hunter.py`.
- **Do not commit**: `.venv/`, generated `routing_config.yaml`.

The core logic is real and tested. The gap between "CLI prototype" and "testable product with UI" is a thin FastAPI layer (~half day) plus a minimal frontend.

---

*Handoff prepared: May 31, 2026*
