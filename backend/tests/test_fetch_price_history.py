"""Tests for pricetoken.ai history fetch helpers."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.engine.backfill_supabase import generate_historical_alerts  # noqa: E402
from backend.engine.fetch_price_history import (  # noqa: E402
    history_catalog_models,
    history_to_snapshot_rows,
)


def test_history_to_snapshot_rows_flattens_points():
    payload = {
        "data": [
            {
                "modelId": "gpt-4o",
                "provider": "openai",
                "history": [
                    {"date": "2026-03-01", "inputPerMTok": 2.5, "outputPerMTok": 10.0},
                    {"date": "2026-03-02", "inputPerMTok": 2.5, "outputPerMTok": 8.0},
                ],
            }
        ],
    }
    rows = history_to_snapshot_rows(payload)
    assert len(rows) == 2
    assert rows[0]["model_id"] == "gpt-4o"
    assert rows[0]["provider_id"] == "openai"
    assert rows[0]["output_per_1m"] == 10.0
    assert rows[1]["fetched_at"] == "2026-03-02T12:00:00Z"
    assert rows[0]["source"] == "pricetoken.ai/history"


def test_history_catalog_models_uses_latest_pricing():
    payload = {
        "data": [
            {
                "modelId": "claude-sonnet",
                "provider": "anthropic",
                "displayName": "Claude Sonnet",
                "history": [
                    {"date": "2026-03-01", "inputPerMTok": 3.0, "outputPerMTok": 15.0},
                    {"date": "2026-03-10", "inputPerMTok": 2.0, "outputPerMTok": 10.0},
                ],
            }
        ],
    }
    models = history_catalog_models(payload)
    assert len(models) == 1
    assert models[0]["display_name"] == "Claude Sonnet"
    assert models[0]["pricing"]["output_per_1m"] == 10.0


def test_generate_historical_alerts_detects_drop():
    rows = [
        {
            "model_id": "gpt-4o-mini",
            "fetched_at": "2026-03-01T12:00:00Z",
            "output_per_1m": 1.0,
        },
        {
            "model_id": "gpt-4o-mini",
            "fetched_at": "2026-03-02T12:00:00Z",
            "output_per_1m": 0.5,
        },
    ]
    alerts = generate_historical_alerts(rows)
    assert len(alerts) == 1
    assert alerts[0]["direction"] == "drop"
    assert alerts[0]["pct_change"] == -50.0
