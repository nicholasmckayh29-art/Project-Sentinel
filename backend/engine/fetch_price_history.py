"""Fetch historical text model pricing from pricetoken.ai."""

from __future__ import annotations

import json
import logging
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

log = logging.getLogger(__name__)

HISTORY_URL = "https://pricetoken.ai/api/v1/text/history"


def _fetch_json(url: str, timeout: int = 120) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "pricing-sentinel/1.0"})
    with urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Expected object response from history API")
    return payload


def fetch_text_price_history(*, days: int = 150) -> dict[str, Any]:
    """Return raw history payload: {data: [{modelId, provider, history: [...]}], meta}."""
    url = f"{HISTORY_URL}?days={days}"
    payload = _fetch_json(url)
    models = payload.get("data", [])
    log.info("Fetched history for %d models (%d days requested)", len(models), days)
    return payload


def history_to_snapshot_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten API history into price_snapshots rows for Supabase."""
    rows: list[dict[str, Any]] = []
    for model in payload.get("data", []):
        model_id = model.get("modelId")
        provider = model.get("provider", "unknown")
        if not model_id:
            continue
        for point in model.get("history", []):
            date = point.get("date")
            if not date:
                continue
            rows.append(
                {
                    "fetched_at": f"{date}T12:00:00Z",
                    "model_id": model_id,
                    "provider_id": provider,
                    "input_per_1m": float(point.get("inputPerMTok", 0)),
                    "output_per_1m": float(point.get("outputPerMTok", 0)),
                    "source": "pricetoken.ai/history",
                }
            )
    return rows


def history_catalog_models(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Minimal model records for catalog upsert from history payload."""
    models: list[dict[str, Any]] = []
    for entry in payload.get("data", []):
        model_id = entry.get("modelId")
        if not model_id:
            continue
        history = entry.get("history") or []
        latest = history[-1] if history else {}
        models.append(
            {
                "model_id": model_id,
                "provider": entry.get("provider", "unknown"),
                "display_name": entry.get("displayName", model_id),
                "pricing": {
                    "input_per_1m": float(latest.get("inputPerMTok", 0)),
                    "output_per_1m": float(latest.get("outputPerMTok", 0)),
                    "currency": "USD",
                },
                "capabilities": {},
                "limits": {},
                "benchmarks": {},
                "metadata": {"data_source": "pricetoken.ai/history"},
            }
        )
    return models
