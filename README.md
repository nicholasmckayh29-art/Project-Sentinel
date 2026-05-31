# Pricing Sentinel

Active intelligence platform that tells you **which AI model to use, when, and why** — not another pricing dashboard.

## What It Does

- **Routine 1 — Price Drop Hunter**: Detects meaningful price shifts using True Cost (not raw token prices)
- **Routine 2 — Release Radar Analyst**: Monitors releases and rumors for wait/switch/hold signals
- **Routine 3 — Stack Optimizer**: Generates opinionated routing configs with projected savings

## Quick Start

```bash
cd pricing-sentinel
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Fetch live prices
python scripts/fetch_prices.py

# Run full Price Drop Hunter flow
python scripts/run_price_hunter.py

# Generate routing config
python scripts/generate_routing_config.py

# Run tests
python -m pytest tests/ -v
```

## Data Sources

| Priority | Source | Endpoint |
|----------|--------|----------|
| Primary | [PriceToken](https://pricetoken.ai) | `GET /api/v1/text` |
| Fallback | [Price Per Token](https://pricepertoken.com) | `GET /api/v1/models` |
| Benchmarks | `data/model_capabilities.json` | Curated overrides |

## Project Structure

```
data/           Live snapshots, baselines, workloads
scripts/        Core logic (fetch, calculate, alert, route)
alerts/         Slack Block Kit + email digest formatters
config/         Cron schedules and alert thresholds
docs/           True Cost formula documentation
```

## Cursor Automation Setup

See `CONTEXT_AI_MODEL_INTELLIGENCE_PLATFORM.md` for full Routine specs. Wire each routine to run its script on the cron schedule in `config/cron_schedules.yaml`.

**Secrets required** (Cursor Secrets): `SLACK_BOT_TOKEN`, `RESEND_API_KEY` (optional for email)

## True Cost

Raw token prices lie. True Cost adjusts for retries, caching, batch discounts, and token efficiency per workload. See [docs/true_cost_formula.md](docs/true_cost_formula.md).

## Phase 1 MVP

- [x] Repository scaffold
- [x] `fetch_prices.py` with live API
- [x] True Cost calculator + tests
- [x] Alert validation + Slack formatter
- [ ] Cursor Routine 1 automation (Slack connector)
- [ ] Baseline drift detection over time
