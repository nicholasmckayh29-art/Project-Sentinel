"""Scan provider changelogs and release feeds (Routine 2 stub)."""

from __future__ import annotations

import json
import logging
import sys
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

RELEASE_FEED_URL = "https://pricepertoken.com/feed"

logging.basicConfig(
    level=logging.INFO,
    format='{"level":"%(levelname)s","message":"%(message)s","ts":"%(asctime)s"}',
)
log = logging.getLogger(__name__)


def fetch_release_feed() -> list[dict[str, Any]]:
    try:
        request = Request(RELEASE_FEED_URL, headers={"User-Agent": "pricing-sentinel/1.0"})
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if isinstance(payload, list):
            return payload
        return payload.get("items", payload.get("releases", []))
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        log.warning("Release feed unavailable: %s", exc)
        return []


def classify_release(item: dict[str, Any]) -> dict[str, Any]:
    title = item.get("title") or item.get("name", "Unknown release")
    return {
        "event_id": item.get("id") or title.lower().replace(" ", "-"),
        "date": item.get("published_at") or item.get("date"),
        "title": title,
        "type": "model_release",
        "impact": "market_shift",
        "models_affected": item.get("models", []),
        "reason": item.get("summary", "New model release"),
        "source": RELEASE_FEED_URL,
        "confidence": 0.85,
        "recommendation": "WAIT & WATCH",
    }


def main() -> int:
    feed_items = fetch_release_feed()
    events = [classify_release(item) for item in feed_items[:20]]
    print(json.dumps({"status": "ok", "event_count": len(events), "events": events[:3]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
