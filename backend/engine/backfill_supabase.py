"""Backfill Supabase price_snapshots from pricetoken.ai historical API."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.engine.fetch_price_history import (  # noqa: E402
    fetch_text_price_history,
    history_catalog_models,
    history_to_snapshot_rows,
)
from backend.engine.supabase_sync import (  # noqa: E402
    bulk_insert_price_snapshots,
    get_supabase_client,
    sync_alerts,
    sync_catalog,
)

logging.basicConfig(
    level=logging.INFO,
    format='{"level":"%(levelname)s","message":"%(message)s","ts":"%(asctime)s"}',
)
log = logging.getLogger(__name__)

HISTORY_SOURCE = "pricetoken.ai/history"
DROP_THRESHOLD_PCT = 15.0


def _delete_history_snapshots(client) -> int:
    result = client.table("price_snapshots").delete().eq("source", HISTORY_SOURCE).execute()
    return len(result.data or [])


def _delete_history_alerts(client) -> int:
    result = (
        client.table("alerts")
        .delete()
        .eq("reason", "historical_price_drop")
        .execute()
    )
    return len(result.data or [])


def generate_historical_alerts(rows: list[dict]) -> list[dict]:
    """Detect day-over-day output price drops from backfilled snapshots."""
    by_model: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_model[row["model_id"]].append(row)

    alerts: list[dict] = []
    for model_id, points in by_model.items():
        points.sort(key=lambda p: p["fetched_at"])
        for prev, curr in zip(points, points[1:]):
            prev_out = prev["output_per_1m"]
            curr_out = curr["output_per_1m"]
            if prev_out <= 0:
                continue
            pct = ((curr_out - prev_out) / prev_out) * 100.0
            if pct > -DROP_THRESHOLD_PCT:
                continue
            alerts.append(
                {
                    "model_id": model_id,
                    "workload_id": None,
                    "direction": "drop",
                    "priority": "critical" if pct <= -25 else "high",
                    "reason": "historical_price_drop",
                    "pct_change": round(pct, 2),
                    "true_cost": round(curr_out / 1000, 6),
                    "baseline_true_cost": round(prev_out / 1000, 6),
                    "display_name": model_id,
                    "workload_name": None,
                    "created_at": curr["fetched_at"],
                    "metadata": {"source": HISTORY_SOURCE, "backfill": True},
                }
            )
    return alerts


def insert_historical_alerts(client, alerts: list[dict]) -> int:
    if not alerts:
        return 0
    batch_size = 200
    inserted = 0
    for i in range(0, len(alerts), batch_size):
        batch = alerts[i : i + batch_size]
        rows = []
        for alert in batch:
            rows.append(
                {
                    "created_at": alert["created_at"],
                    "model_id": alert["model_id"],
                    "workload_id": alert.get("workload_id"),
                    "direction": alert["direction"],
                    "priority": alert.get("priority", "high"),
                    "reason": alert.get("reason", "historical_price_drop"),
                    "pct_change": alert.get("pct_change"),
                    "true_cost": alert.get("true_cost"),
                    "baseline_true_cost": alert.get("baseline_true_cost"),
                    "display_name": alert.get("display_name"),
                    "workload_name": alert.get("workload_name"),
                    "metadata": alert.get("metadata", {}),
                }
            )
        client.table("alerts").insert(rows).execute()
        inserted += len(rows)
    return inserted


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backfill YTD price history into Supabase")
    parser.add_argument("--days", type=int, default=150, help="Days of history (default 150)")
    parser.add_argument("--force", action="store_true", help="Delete prior history backfill rows first")
    parser.add_argument("--with-alerts", action="store_true", help="Generate historical drop alerts")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and summarize only")
    args = parser.parse_args(argv)

    payload = fetch_text_price_history(days=args.days)
    rows = history_to_snapshot_rows(payload)
    meta = payload.get("meta", {})
    dates = sorted({r["fetched_at"][:10] for r in rows})

    summary = {
        "models": len(payload.get("data", [])),
        "snapshot_rows": len(rows),
        "date_range": [dates[0], dates[-1]] if dates else [],
        "meta": meta,
    }

    if args.dry_run:
        print(json.dumps(summary, indent=2))
        return 0

    client = get_supabase_client()
    if client is None:
        log.error("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
        return 1

    if args.force:
        deleted = _delete_history_snapshots(client)
        log.info("Deleted %d prior history snapshot rows", deleted)
        if args.with_alerts:
            deleted_alerts = _delete_history_alerts(client)
            log.info("Deleted %d prior historical alerts", deleted_alerts)

    catalog = history_catalog_models(payload)
    sync_catalog(client, catalog)
    inserted = bulk_insert_price_snapshots(client, rows)

    alert_count = 0
    if args.with_alerts:
        alerts = generate_historical_alerts(rows)
        alert_count = insert_historical_alerts(client, alerts)

    output = {
        **summary,
        "inserted_snapshots": inserted,
        "historical_alerts": alert_count,
        "note": "PriceToken history typically starts ~March 2026, not Jan 1.",
    }
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
