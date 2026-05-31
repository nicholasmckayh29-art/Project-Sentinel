"""FastAPI application exposing Pricing Sentinel CLI logic over HTTP."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.engine.generate_routing_config import get_routing_config  # noqa: E402
from backend.engine.run_price_hunter import run_price_hunter  # noqa: E402

DATA_DIR = ROOT / "data"
CURRENT_PRICES_PATH = DATA_DIR / "current_prices.json"
ALERT_HISTORY_PATH = DATA_DIR / "alert_history.json"

app = FastAPI(title="Pricing Sentinel", version="1.0.0")


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {path.name}")
    with path.open() as handle:
        return json.load(handle)


@app.get("/api/models")
def get_models() -> dict[str, Any]:
    """Return the latest model pricing snapshot."""
    return _load_json(CURRENT_PRICES_PATH)


@app.get("/api/alerts")
def get_alerts() -> dict[str, Any]:
    """Return alert history."""
    if not ALERT_HISTORY_PATH.exists():
        return {"alerts": []}
    return _load_json(ALERT_HISTORY_PATH)


@app.get("/api/routing")
def get_routing() -> dict[str, Any]:
    """Return routing config, generating it from current prices if needed."""
    try:
        return get_routing_config()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/refresh")
def refresh_prices() -> dict[str, Any]:
    """Fetch live prices and run the Price Drop Hunter pipeline."""
    try:
        return run_price_hunter()
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
