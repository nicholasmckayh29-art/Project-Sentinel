"""Tests for demo price alert simulation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.engine.demo_price_alert import inflate_baseline_for_model, run_demo_alert  # noqa: E402


def test_inflate_baseline_doubles_output_price():
    baselines = {
        "snapshots": [
            {
                "model_id": "gpt-4o-mini",
                "pricing": {"input_per_1m": 0.15, "output_per_1m": 0.6},
            }
        ]
    }
    demo = inflate_baseline_for_model(baselines, "gpt-4o-mini", inflate_factor=2.0)
    snapshot = demo["snapshots"][0]
    assert snapshot["pricing"]["output_per_1m"] == 1.2
    assert snapshot["pricing"]["input_per_1m"] == 0.3


def test_run_demo_alert_triggers_for_default_model():
    result = run_demo_alert(model_id="claude-haiku-4-5-20251001", inflate_factor=2.0)
    assert result["status"] == "ok"
    assert result["alert_count"] >= 1
    alert = result["alerts"][0]
    assert alert["trigger"] is True
    assert alert["reason"] == "significant_price_drop"
    assert alert.get("slack_blocks")


def test_demo_main_json_only_exits_zero(capsys):
    from backend.engine import demo_price_alert

    result = demo_price_alert.main(
        ["--model-id", "gpt-4o-mini", "--inflate-factor", "2.0", "--json-only"]
    )
    assert result == 0
    captured = capsys.readouterr().out.strip()
    payload = json.loads(captured)
    assert payload["alert_count"] >= 1
