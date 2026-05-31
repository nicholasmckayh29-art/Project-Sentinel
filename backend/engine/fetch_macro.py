"""Fetch macro snapshots from FRED API."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any
from urllib.request import Request, urlopen

log = logging.getLogger(__name__)

FRED_SERIES = {
    "DGS10": "10Y Treasury Yield",
    "VIXCLS": "VIX Close",
}


def _fetch_fred_series(series_id: str, api_key: str) -> dict[str, Any] | None:
    url = (
        f"https://api.stlouisfed.org/fred/series/observations"
        f"?series_id={series_id}&api_key={api_key}&file_type=json&sort_order=desc&limit=2"
    )
    request = Request(url, headers={"User-Agent": "pricing-sentinel/1.0"})
    with urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode())
    observations = [o for o in payload.get("observations", []) if o.get("value") != "."]
    if not observations:
        return None
    latest = observations[0]
    value = float(latest["value"])
    change_pct = None
    if len(observations) > 1:
        prev = float(observations[1]["value"])
        if prev:
            change_pct = round((value - prev) / prev * 100, 2)
    return {
        "series_id": series_id,
        "label": FRED_SERIES.get(series_id, series_id),
        "value": value,
        "change_pct": change_pct,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def fetch_macro_snapshots() -> list[dict[str, Any]]:
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        log.info("FRED_API_KEY not set — skipping macro fetch")
        return []
    snapshots: list[dict[str, Any]] = []
    for series_id in FRED_SERIES:
        try:
            snap = _fetch_fred_series(series_id, api_key)
            if snap:
                snapshots.append(snap)
        except Exception as exc:
            log.warning("FRED fetch failed for %s: %s", series_id, exc)
    return snapshots
