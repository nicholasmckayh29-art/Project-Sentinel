"""Fetch community and labor market signals."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any
from urllib.request import Request, urlopen

log = logging.getLogger(__name__)

HF_MODELS = "https://huggingface.co/api/models?sort=downloads&direction=-1&limit=10"
AI_JOBS_RSS = "https://aidevboard.com/feed.xml"


def fetch_hf_trending() -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    try:
        request = Request(HF_MODELS, headers={"User-Agent": "pricing-sentinel/1.0"})
        with urlopen(request, timeout=20) as response:
            models = json.loads(response.read().decode())
        for model in models[:5]:
            name = model.get("modelId") or model.get("id", "unknown")
            downloads = model.get("downloads", 0)
            signals.append(
                {
                    "signal_type": "hf_trending",
                    "label": name,
                    "value": float(downloads),
                    "metadata": {"source_api": "huggingface", "model_id": name},
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                }
            )
    except Exception as exc:
        log.warning("HF trending fetch failed: %s", exc)
    return signals


def fetch_ai_jobs_count() -> list[dict[str, Any]]:
    try:
        import feedparser
    except ImportError:
        return []
    try:
        parsed = feedparser.parse(AI_JOBS_RSS)
        count = len(parsed.entries)
        return [
            {
                "signal_type": "ai_jobs_count",
                "label": "AI Dev Jobs (feed)",
                "value": float(count),
                "metadata": {"source_api": "aidevboard", "rss_url": AI_JOBS_RSS},
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
        ]
    except Exception as exc:
        log.warning("AI jobs fetch failed: %s", exc)
        return []


def fetch_community_signals() -> list[dict[str, Any]]:
    return fetch_hf_trending() + fetch_ai_jobs_count()
