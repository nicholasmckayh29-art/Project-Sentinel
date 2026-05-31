"""Tests for the FastAPI HTTP API."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.api.main import CURRENT_PRICES_PATH, app  # noqa: E402

client = TestClient(app)


def test_get_models_returns_current_prices():
    response = client.get("/api/models")
    assert response.status_code == 200
    payload = response.json()
    assert "models" in payload
    assert "model_count" in payload
    assert payload["model_count"] == len(payload["models"])
    assert payload["model_count"] > 0


def test_get_models_missing_file(tmp_path, monkeypatch):
    missing = tmp_path / "current_prices.json"
    monkeypatch.setattr("backend.api.main.CURRENT_PRICES_PATH", missing)
    response = client.get("/api/models")
    assert response.status_code == 404


def test_get_alerts_returns_history():
    response = client.get("/api/alerts")
    assert response.status_code == 200
    payload = response.json()
    assert "alerts" in payload
    assert isinstance(payload["alerts"], list)


def test_get_alerts_empty_when_file_missing(tmp_path, monkeypatch):
    missing = tmp_path / "alert_history.json"
    monkeypatch.setattr("backend.api.main.ALERT_HISTORY_PATH", missing)
    response = client.get("/api/alerts")
    assert response.status_code == 200
    assert response.json() == {"alerts": []}


def test_get_routing_returns_config():
    response = client.get("/api/routing")
    assert response.status_code == 200
    payload = response.json()
    assert "routes" in payload
    assert "projections" in payload
    assert isinstance(payload["routes"], list)


def test_get_routing_generates_when_missing(tmp_path, monkeypatch):
    routing_path = tmp_path / "routing_config.yaml"

    monkeypatch.setattr("backend.engine.generate_routing_config.OUTPUT_PATH", routing_path)

    response = client.get("/api/routing")
    assert response.status_code == 200
    payload = response.json()
    assert "routes" in payload
    assert routing_path.exists()


@patch("backend.api.main.run_price_hunter")
def test_post_refresh_runs_pipeline(mock_run):
    mock_run.return_value = {
        "status": "ok",
        "fetched_at": "2026-05-31T12:00:00Z",
        "model_count": 41,
        "alert_count": 0,
        "alerts": [],
    }
    response = client.post("/api/refresh")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["model_count"] == 41
    assert payload["alert_count"] == 0
    mock_run.assert_called_once()


@patch("backend.api.main.run_price_hunter")
def test_post_refresh_handles_fetch_failure(mock_run):
    mock_run.side_effect = RuntimeError("All pricing sources failed")
    response = client.post("/api/refresh")
    assert response.status_code == 502
    assert "All pricing sources failed" in response.json()["detail"]
