"""Tests for SQLite price snapshot history."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.engine.price_history import (  # noqa: E402
    get_price_trend,
    init_db,
    list_recent_snapshots,
    record_alert_events,
    record_snapshot,
)


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "test_price_history.db"
    init_db(path)
    return path


def _sample_snapshot(
    fetched_at: str,
    model_id: str = "gpt-4o-mini",
    input_price: float = 0.15,
    output_price: float = 0.60,
) -> dict:
    return {
        "fetched_at": fetched_at,
        "source": "pricetoken.ai",
        "model_count": 1,
        "models": [
            {
                "model_id": model_id,
                "provider": "openai",
                "pricing": {
                    "input_per_1m": input_price,
                    "output_per_1m": output_price,
                    "currency": "USD",
                },
                "metadata": {"data_source": "pricetoken.ai"},
            }
        ],
    }


def test_record_snapshot_inserts_rows(db_path: Path):
    snapshot = _sample_snapshot("2026-05-31T12:00:00Z")
    count = record_snapshot(snapshot, db_path=db_path)
    assert count == 1

    runs = list_recent_snapshots(limit=5, db_path=db_path)
    assert len(runs) == 1
    assert runs[0]["timestamp"] == "2026-05-31T12:00:00Z"
    assert runs[0]["model_count"] == 1
    assert runs[0]["source"] == "pricetoken.ai"


def test_record_snapshot_multiple_models(db_path: Path):
    snapshot = {
        "fetched_at": "2026-05-31T12:00:00Z",
        "source": "pricetoken.ai",
        "model_count": 2,
        "models": [
            _sample_snapshot("2026-05-31T12:00:00Z")["models"][0],
            _sample_snapshot(
                "2026-05-31T12:00:00Z",
                model_id="claude-haiku-4-5-20251001",
                input_price=1.0,
                output_price=5.0,
            )["models"][0],
        ],
    }
    assert record_snapshot(snapshot, db_path=db_path) == 2


def test_get_price_trend_over_days(db_path: Path):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    old_ts = (now - timedelta(days=10)).isoformat().replace("+00:00", "Z")
    recent_ts = (now - timedelta(days=2)).isoformat().replace("+00:00", "Z")
    stale_ts = (now - timedelta(days=40)).isoformat().replace("+00:00", "Z")

    record_snapshot(_sample_snapshot(stale_ts, output_price=1.0), db_path=db_path)
    record_snapshot(_sample_snapshot(old_ts, output_price=0.55), db_path=db_path)
    record_snapshot(_sample_snapshot(recent_ts, output_price=0.50), db_path=db_path)

    trend = get_price_trend("gpt-4o-mini", days=30, db_path=db_path)
    assert len(trend) == 2
    assert trend[0]["output_per_1m"] == 0.55
    assert trend[1]["output_per_1m"] == 0.50


def test_get_price_trend_empty_for_unknown_model(db_path: Path):
    record_snapshot(_sample_snapshot("2026-05-31T12:00:00Z"), db_path=db_path)
    trend = get_price_trend("unknown-model", days=7, db_path=db_path)
    assert trend == []


def test_record_alert_events_links_snapshot(db_path: Path):
    ts = "2026-05-31T12:00:00Z"
    record_snapshot(_sample_snapshot(ts), db_path=db_path)

    alerts = [
        {
            "model_id": "gpt-4o-mini",
            "workload_id": "coding_assistant",
            "priority": "high",
            "reason": "significant_price_drop",
        }
    ]
    count = record_alert_events(alerts, snapshot_timestamp=ts, db_path=db_path)
    assert count == 1

    import sqlite3

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT snapshot_id, model_id, reason FROM alert_events"
        ).fetchone()
    assert row["model_id"] == "gpt-4o-mini"
    assert row["reason"] == "significant_price_drop"
    assert row["snapshot_id"] is not None


def test_list_recent_snapshots_respects_limit(db_path: Path):
    for day in range(5):
        ts = f"2026-05-{day + 1:02d}T12:00:00Z"
        record_snapshot(_sample_snapshot(ts), db_path=db_path)

    runs = list_recent_snapshots(limit=3, db_path=db_path)
    assert len(runs) == 3
    assert runs[0]["timestamp"] > runs[-1]["timestamp"]
