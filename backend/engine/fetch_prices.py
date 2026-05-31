"""Fetch live model pricing from public APIs and write current_prices.json."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data"
CAPABILITIES_PATH = DATA_DIR / "model_capabilities.json"
OUTPUT_PATH = DATA_DIR / "current_prices.json"

PRIMARY_URL = "https://pricetoken.ai/api/v1/text"
FALLBACK_URL = "https://pricepertoken.com/api/v1/models"

PROVIDER_CAPABILITIES: dict[str, dict[str, bool]] = {
    "anthropic": {
        "vision": True,
        "json_mode": True,
        "function_calling": True,
        "streaming": True,
        "caching": True,
        "batch_api": True,
    },
    "openai": {
        "vision": True,
        "json_mode": True,
        "function_calling": True,
        "streaming": True,
        "caching": True,
        "batch_api": True,
    },
    "google": {
        "vision": True,
        "json_mode": True,
        "function_calling": True,
        "streaming": True,
        "caching": True,
        "batch_api": False,
    },
    "deepseek": {
        "vision": False,
        "json_mode": True,
        "function_calling": True,
        "streaming": True,
        "caching": False,
        "batch_api": False,
    },
    "xai": {
        "vision": True,
        "json_mode": True,
        "function_calling": True,
        "streaming": True,
        "caching": False,
        "batch_api": False,
    },
}

DEFAULT_CAPABILITIES = {
    "vision": False,
    "json_mode": True,
    "function_calling": True,
    "streaming": True,
    "caching": False,
    "batch_api": False,
}

logging.basicConfig(
    level=logging.INFO,
    format='{"level":"%(levelname)s","message":"%(message)s","ts":"%(asctime)s"}',
)
log = logging.getLogger(__name__)


def _fetch_json(url: str, timeout: int = 30) -> dict[str, Any] | list[Any]:
    request = Request(url, headers={"User-Agent": "pricing-sentinel/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _load_capability_overrides() -> dict[str, dict[str, Any]]:
    if not CAPABILITIES_PATH.exists():
        return {}
    with CAPABILITIES_PATH.open() as handle:
        payload = json.load(handle)
    return {entry["model_id"]: entry for entry in payload.get("models", [])}


def apply_capability_overrides(models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge local benchmark and efficiency overrides into price snapshot models."""
    overrides = _load_capability_overrides()
    if not overrides:
        return models

    merged: list[dict[str, Any]] = []
    for model in models:
        override = overrides.get(model["model_id"], {})
        if not override:
            merged.append(model)
            continue

        entry = {**model}
        if override.get("benchmarks"):
            entry["benchmarks"] = {**model.get("benchmarks", {}), **override["benchmarks"]}
        if override.get("capabilities"):
            entry["capabilities"] = {**model.get("capabilities", {}), **override["capabilities"]}
        if override.get("metadata"):
            entry["metadata"] = {**model.get("metadata", {}), **override["metadata"]}
        if override.get("limits"):
            entry["limits"] = {**model.get("limits", {}), **override["limits"]}
        merged.append(entry)
    return merged


def _normalize_pricetoken(record: dict[str, Any], overrides: dict[str, dict[str, Any]]) -> dict[str, Any]:
    model_id = record["modelId"]
    provider = record["provider"]
    override = overrides.get(model_id, {})
    capabilities = {
        **PROVIDER_CAPABILITIES.get(provider, DEFAULT_CAPABILITIES),
        **override.get("capabilities", {}),
    }
    benchmarks = override.get("benchmarks", {})
    metadata = override.get("metadata", {})
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    return {
        "model_id": model_id,
        "provider": provider,
        "display_name": record.get("displayName", model_id),
        "timestamp": timestamp,
        "pricing": {
            "input_per_1m": float(record["inputPerMTok"]),
            "output_per_1m": float(record["outputPerMTok"]),
            "currency": "USD",
        },
        "capabilities": capabilities,
        "limits": {
            "context_window_tokens": record.get("contextWindow"),
            "max_output_tokens": record.get("maxOutputTokens"),
            "rate_limit_rpm": override.get("limits", {}).get("rate_limit_rpm"),
        },
        "benchmarks": benchmarks,
        "metadata": {
            "release_date": record.get("launchDate"),
            "status": record.get("status", "active"),
            "successor_rumored": metadata.get("successor_rumored", False),
            "efficiency_ratio": metadata.get("efficiency_ratio", 1.0),
            "source_confidence": record.get("confidenceLevel", "unknown"),
            "data_source": "pricetoken.ai",
        },
    }


def _normalize_pricepertoken(record: dict[str, Any], overrides: dict[str, dict[str, Any]]) -> dict[str, Any]:
    model_id = record.get("id") or record.get("model_id", "unknown")
    provider = record.get("provider") or record.get("author", "unknown")
    override = overrides.get(model_id, {})
    pricing = record.get("pricing", record)
    capabilities = {
        **PROVIDER_CAPABILITIES.get(provider, DEFAULT_CAPABILITIES),
        **override.get("capabilities", {}),
    }
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    return {
        "model_id": model_id,
        "provider": provider,
        "display_name": record.get("name", model_id),
        "timestamp": timestamp,
        "pricing": {
            "input_per_1m": float(pricing.get("input_per_1m", pricing.get("input", 0))),
            "output_per_1m": float(pricing.get("output_per_1m", pricing.get("output", 0))),
            "currency": "USD",
        },
        "capabilities": capabilities,
        "limits": override.get("limits", {}),
        "benchmarks": override.get("benchmarks", {}),
        "metadata": {
            **override.get("metadata", {}),
            "data_source": "pricepertoken.com",
        },
    }


def fetch_from_primary(overrides: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    payload = _fetch_json(PRIMARY_URL)
    records = payload.get("data", payload)
    models = [_normalize_pricetoken(record, overrides) for record in records]
    active = [model for model in models if model["metadata"].get("status") != "deprecated"]
    log.info("Fetched %d active models from pricetoken.ai", len(active))
    return active


def fetch_from_fallback(overrides: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    payload = _fetch_json(FALLBACK_URL)
    if isinstance(payload, dict):
        records = payload.get("models", payload.get("data", []))
    else:
        records = payload
    models = [_normalize_pricepertoken(record, overrides) for record in records]
    log.info("Fetched %d models from pricepertoken.com fallback", len(models))
    return models


def fetch_prices() -> dict[str, Any]:
    overrides = _load_capability_overrides()
    source = "pricetoken.ai"
    try:
        models = fetch_from_primary(overrides)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
        log.warning("Primary source failed (%s), trying fallback", exc)
        try:
            models = fetch_from_fallback(overrides)
            source = "pricepertoken.com"
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, KeyError) as fallback_exc:
            raise RuntimeError(
                f"All pricing sources failed: primary={exc}, fallback={fallback_exc}"
            ) from fallback_exc

    snapshot = {
        "fetched_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source": source,
        "model_count": len(models),
        "models": models,
    }
    return snapshot


def write_prices(snapshot: dict[str, Any], output_path: Path = OUTPUT_PATH) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as handle:
        json.dump(snapshot, handle, indent=2)
        handle.write("\n")
    log.info("Wrote %d models to %s", snapshot["model_count"], output_path)
    return output_path


def main() -> int:
    try:
        snapshot = fetch_prices()
        write_prices(snapshot)
        print(json.dumps({"status": "ok", "model_count": snapshot["model_count"]}))
        return 0
    except Exception as exc:
        log.exception("fetch_prices failed")
        print(json.dumps({"status": "error", "message": str(exc)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
