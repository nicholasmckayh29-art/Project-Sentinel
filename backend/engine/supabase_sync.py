"""Sync price hunter output to Supabase Postgres."""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime, timezone
from typing import Any

log = logging.getLogger(__name__)


def normalize_supabase_url(url: str) -> str:
    """Accept API URL or dashboard URL; return canonical API URL."""
    url = url.strip().rstrip("/")
    if "/dashboard/project/" in url:
        project_ref = url.split("/dashboard/project/")[-1].split("/")[0]
        return f"https://{project_ref}.supabase.co"
    if url.startswith("http") and ".supabase.co" in url:
        return url
    if url and not url.startswith("http") and "." not in url:
        # bare project ref, e.g. eamkkmlpphsimvznjjcf
        return f"https://{url}.supabase.co"
    return url


def get_supabase_client():
    raw_url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not raw_url or not key:
        return None
    url = normalize_supabase_url(raw_url)
    if ".supabase.co" not in url:
        raise ValueError(
            "SUPABASE_URL must be your project API URL, e.g. "
            "https://eamkkmlpphsimvznjjcf.supabase.co "
            "(Project Settings → API → Project URL). "
            f"Got: {raw_url!r}"
        )
    from supabase import create_client

    return create_client(url, key)


def _parse_ts(value: str) -> str:
    return value.replace("Z", "+00:00") if value.endswith("Z") else value


def sync_catalog(client, models: list[dict[str, Any]]) -> None:
    providers_seen: set[str] = set()
    for model in models:
        provider_id = model.get("provider", "unknown")
        if provider_id not in providers_seen:
            client.table("providers").upsert(
                {"id": provider_id, "display_name": provider_id.title()}
            ).execute()
            providers_seen.add(provider_id)

        client.table("models").upsert(
            {
                "id": model["model_id"],
                "provider_id": provider_id,
                "display_name": model.get("display_name", model["model_id"]),
                "pricing": model.get("pricing", {}),
                "capabilities": model.get("capabilities", {}),
                "limits": model.get("limits", {}),
                "benchmarks": model.get("benchmarks", {}),
                "metadata": model.get("metadata", {}),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        ).execute()

        efficiency = model.get("metadata", {}).get("efficiency_ratio", 1.0)
        if model.get("benchmarks"):
            client.table("model_capabilities").upsert(
                {
                    "model_id": model["model_id"],
                    "benchmarks": model["benchmarks"],
                    "efficiency_ratio": efficiency,
                    "source": model.get("metadata", {}).get("data_source", "live"),
                }
            ).execute()


def sync_price_snapshots(client, snapshot: dict[str, Any]) -> int:
    fetched_at = _parse_ts(snapshot["fetched_at"])
    source = snapshot.get("source", "pricetoken.ai")
    rows = []
    for model in snapshot.get("models", []):
        pricing = model.get("pricing", {})
        rows.append(
            {
                "fetched_at": fetched_at,
                "model_id": model["model_id"],
                "provider_id": model.get("provider", "unknown"),
                "input_per_1m": pricing.get("input_per_1m", 0),
                "output_per_1m": pricing.get("output_per_1m", 0),
                "source": source,
            }
        )
    return bulk_insert_price_snapshots(client, rows)


def bulk_insert_price_snapshots(client, rows: list[dict[str, Any]], *, batch_size: int = 500) -> int:
    """Insert snapshot rows in batches. Returns total inserted."""
    if not rows:
        return 0
    inserted = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        client.table("price_snapshots").insert(batch).execute()
        inserted += len(batch)
    return inserted


def sync_baselines(client, baselines: dict[str, Any]) -> int:
    count = 0
    for entry in baselines.get("snapshots", []):
        client.table("baselines").upsert(
            {
                "model_id": entry["model_id"],
                "captured_at": _parse_ts(entry.get("captured_at", baselines.get("updated_at", ""))),
                "pricing": entry.get("pricing", {}),
                "benchmarks": entry.get("benchmarks", {}),
                "capabilities": entry.get("capabilities", {}),
                "metadata": entry.get("metadata", {}),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        ).execute()
        count += 1
    return count


def sync_alerts(client, alerts: list[dict[str, Any]]) -> int:
    if not alerts:
        return 0
    rows = []
    for alert in alerts:
        pct = alert.get("pct_change")
        direction = "drop"
        if pct is not None and pct > 0:
            direction = "increase"
        rows.append(
            {
                "model_id": alert["model_id"],
                "workload_id": alert.get("workload_id"),
                "direction": direction,
                "priority": alert.get("priority", "high"),
                "reason": alert.get("reason", "significant_price_drop"),
                "pct_change": pct,
                "true_cost": alert.get("true_cost"),
                "baseline_true_cost": alert.get("baseline_true_cost"),
                "quality_delta_pct": alert.get("quality_delta_pct"),
                "savings_vs_leader_pct": alert.get("savings_vs_leader_pct"),
                "leader_model_id": alert.get("leader_model_id"),
                "display_name": alert.get("display_name"),
                "workload_name": alert.get("workload_name"),
                "metadata": {
                    "slack_blocks": alert.get("slack_blocks"),
                    "action": alert.get("action"),
                },
            }
        )
    client.table("alerts").insert(rows).execute()
    return len(rows)


def sync_workloads(client, workloads: list[dict[str, Any]]) -> None:
    for workload in workloads:
        client.table("workloads").upsert(
            {
                "id": workload["workload_id"],
                "name": workload["name"],
                "workload_type": workload.get("workload_type", "general"),
                "characteristics": workload.get("characteristics", {}),
                "tier": workload.get("tier"),
            }
        ).execute()


def sync_hunter_result(
    client,
    *,
    snapshot: dict[str, Any],
    baselines: dict[str, Any],
    alerts: list[dict[str, Any]],
    workloads: list[dict[str, Any]],
) -> dict[str, int]:
    sync_workloads(client, workloads)
    sync_catalog(client, snapshot.get("models", []))
    return {
        "snapshots": sync_price_snapshots(client, snapshot),
        "baselines": sync_baselines(client, baselines),
        "alerts": sync_alerts(client, alerts),
    }


def _url_hash(url: str | None) -> str | None:
    if not url:
        return None
    return hashlib.sha256(url.strip().encode()).hexdigest()


def sync_market_events(client, events: list[dict[str, Any]]) -> int:
    """Upsert market events deduped by url_hash."""
    if not events:
        return 0
    synced = 0
    for event in events:
        url = event.get("url")
        url_hash = event.get("url_hash") or _url_hash(url)
        row: dict[str, Any] = {
            "title": event["title"],
            "summary": event.get("summary"),
            "event_type": event.get("event_type", "news"),
            "source": event.get("source"),
            "url": url,
            "published_at": _parse_ts(event.get("published_at", datetime.now(timezone.utc).isoformat())),
            "metadata": event.get("metadata", {}),
        }
        if url_hash:
            row["url_hash"] = url_hash
            client.table("market_events").upsert(row, on_conflict="url_hash").execute()
        else:
            client.table("market_events").insert(row).execute()
        synced += 1
    return synced


def sync_market_quotes(client, quotes: list[dict[str, Any]]) -> int:
    if not quotes:
        return 0
    for quote in quotes:
        client.table("market_quotes").upsert(
            {
                "symbol": quote["symbol"],
                "name": quote.get("name", quote["symbol"]),
                "price": quote.get("price"),
                "change_pct": quote.get("change_pct"),
                "fetched_at": _parse_ts(quote.get("fetched_at", datetime.now(timezone.utc).isoformat())),
                "metadata": quote.get("metadata", {}),
            }
        ).execute()
    return len(quotes)


def sync_macro_snapshots(client, snapshots: list[dict[str, Any]]) -> int:
    if not snapshots:
        return 0
    for snap in snapshots:
        client.table("macro_snapshots").upsert(
            {
                "series_id": snap["series_id"],
                "label": snap.get("label", snap["series_id"]),
                "value": snap.get("value"),
                "change_pct": snap.get("change_pct"),
                "fetched_at": _parse_ts(snap.get("fetched_at", datetime.now(timezone.utc).isoformat())),
            }
        ).execute()
    return len(snapshots)


def sync_community_signals(client, signals: list[dict[str, Any]]) -> int:
    if not signals:
        return 0
    rows = []
    for signal in signals:
        rows.append(
            {
                "signal_type": signal["signal_type"],
                "label": signal["label"],
                "value": signal.get("value"),
                "metadata": signal.get("metadata", {}),
                "fetched_at": _parse_ts(signal.get("fetched_at", datetime.now(timezone.utc).isoformat())),
            }
        )
    client.table("community_signals").insert(rows).execute()
    return len(rows)


def sync_routing_recommendations(client, config: dict[str, Any]) -> int:
    routes = config.get("routes", [])
    if not routes:
        return 0
    generated_at = datetime.now(timezone.utc).isoformat()
    projections = config.get("projections", {})
    count = 0
    for route in routes:
        workload_id = route.get("workload_id")
        if not workload_id:
            continue
        client.table("routing_recommendations").insert(
            {
                "workload_id": workload_id,
                "models": route.get("models", []),
                "projections": projections,
                "generated_at": generated_at,
            }
        ).execute()
        count += 1
    return count
