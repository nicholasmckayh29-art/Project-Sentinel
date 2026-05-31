# AI Model Intelligence Platform — Full Context Handoff for Cursor Agents

> **Version**: 1.1  
> **Date**: May 31, 2026  
> **Status**: Ready for Implementation (MVP Phase 1)  
> **Goal**: Build an *active intelligence platform*—not a dashboard—that tells users **which model to use, when, and why**, using autonomous Cursor Automations ("Routines").

---

## Core Philosophy: "Selling the Shovel in the Gold Rush"

The AI model market is the most volatile pricing landscape in tech. Existing tools solve the **data layer** well—but none solve the **decision layer**.

### What Exists (Reference Only)

| Tool | Strengths |
|------|-----------|
| [pricepertoken.com](https://pricepertoken.com) | 300+ models, daily updates, release feed, benchmark trends |
| [itoolverse.com](https://itoolverse.com/data/ai-cost-analyzer) | 189 models, capability filters, stack builder, cost calculator |
| [swfte.com/ai/pricing](https://swfte.com/ai/pricing) | Historical charts, blended cost calc, value score |
| [usagepricing.com](https://usagepricing.com/ai-token-pricing) | Clean input/output breakdown, 50+ models |

These are **inputs**, not outputs. Our product turns inputs into **actionable signals**.

---

## The 7 Gaps We Fill

| # | Gap | Our Solution |
|---|-----|--------------|
| 1 | Timing Intelligence | Routine 2: Release Radar Analyst |
| 2 | Price Change Alerts | Routine 1: Price Drop Hunter |
| 3 | Use-Case-First Recommendations | Routine 3: Stack Optimizer |
| 4 | Price History with Context | Store every price point + market event annotations |
| 5 | True Cost-Effectiveness Scoring | `True Cost = (Price × Amplification × Retry) / (Cache × Batch)` |
| 6 | Opinionated Stack Builder | Recommendation engine with traffic splits |
| 7 | Model Release Radar | Strategic wait/switch/hold signals |

---

## Repository Structure

```
pricing-sentinel/
├── data/
│   ├── current_prices.json
│   ├── baselines.json
│   ├── workloads.json
│   ├── model_capabilities.json
│   └── market_events.json
├── scripts/
│   ├── fetch_prices.py
│   ├── calculate_true_cost.py
│   ├── check_releases.py
│   ├── generate_routing_config.py
│   └── validate_alerts.py
├── alerts/
│   ├── slack_formatter.py
│   └── email_digest.py
├── config/
│   ├── cron_schedules.yaml
│   └── threshold_rules.json
├── docs/
│   └── true_cost_formula.md
└── README.md
```

---

## Phase 1 Execution Plan

**MVP Goal**: By end of Week 2, the system autonomously detects and alerts on a real price drop with True Cost justification.

Start with Routine 1. Validate the True Cost math. Then scale.
