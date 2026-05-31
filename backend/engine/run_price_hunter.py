"""Orchestrate Routine 1: fetch prices, compare to baselines, emit alerts."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.alerts.slack_client import deliver_slack_alerts  # noqa: E402
from backend.alerts.slack_formatter import format_price_alert  # noqa: E402
from backend.engine.calculate_true_cost import meets_quality_requirements, true_cost  # noqa: E402
from backend.engine.fetch_prices import fetch_prices, write_prices  # noqa: E402
from backend.engine.price_history import record_alert_events, record_snapshot  # noqa: E402
from backend.engine.validate_alerts import find_leader, scan_for_alerts  # noqa: E402

DATA_DIR = ROOT / "data"
CONFIG_DIR = ROOT / "config"
BASELINES_PATH = DATA_DIR / "baselines.json"
WORKLOADS_PATH = DATA_DIR / "workloads.json"
THRESHOLDS_PATH = CONFIG_DIR / "threshold_rules.json"
ALERTS_LOG_PATH = DATA_DIR / "alert_history.json"

logging.basicConfig(
    level=logging.INFO,
    format='{"level":"%(levelname)s","message":"%(message)s","ts":"%(asctime)s"}',
)
log = logging.getLogger(__name__)


def _load_json(path: Path, default: dict | list | None = None):
    if not path.exists():
        return default if default is not None else {}
    with path.open() as handle:
        return json.load(handle)


def _save_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def update_baselines(snapshot: dict[str, Any], baselines: dict[str, Any]) -> dict[str, Any]:
    """Append snapshot entries for models not yet tracked; preserve existing baselines."""
    snapshots = {entry["model_id"]: entry for entry in baselines.get("snapshots", [])}
    model_ids = set(baselines.get("model_ids", []))

    for model in snapshot.get("models", []):
        model_id = model["model_id"]
        model_ids.add(model_id)
        if model_id not in snapshots:
            snapshots[model_id] = {
                "model_id": model_id,
                "captured_at": snapshot["fetched_at"],
                "pricing": model["pricing"],
                "benchmarks": model.get("benchmarks", {}),
                "capabilities": model.get("capabilities", {}),
                "metadata": model.get("metadata", {}),
            }

    return {
        "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "model_ids": sorted(model_ids),
        "snapshots": list(snapshots.values()),
    }


def enrich_alerts(alerts: list[dict], models: list[dict], workloads: list[dict]) -> list[dict]:
    model_map = {model["model_id"]: model for model in models}
    workload_map = {workload["workload_id"]: workload for workload in workloads}
    enriched = []

    for alert in alerts:
        model = model_map.get(alert["model_id"])
        workload = workload_map.get(alert["workload_id"])
        if not model or not workload:
            continue
        if not meets_quality_requirements(model, workload):
            continue

        leader = find_leader(models, workload)
        leader_cost = true_cost(leader, workload) if leader else 0.0
        savings_pct = 0.0
        if leader_cost > 0 and alert.get("true_cost") is not None:
            savings_pct = ((leader_cost - alert["true_cost"]) / leader_cost) * 100.0

        enriched.append(
            {
                **alert,
                "savings_vs_leader_pct": round(max(savings_pct, 0.0), 2),
                "leader_model_id": leader.get("model_id") if leader else None,
                "slack_blocks": format_price_alert(
                    model_name=alert.get("display_name", alert["model_id"]),
                    savings_pct=alert.get("pct_change", savings_pct),
                    workload_name=alert.get("workload_name", alert["workload_id"]),
                    true_cost=alert.get("true_cost", 0.0),
                    baseline_true_cost=alert.get("baseline_true_cost", 0.0),
                    action=_action_for_alert(alert),
                    model_id=alert["model_id"],
                    priority=alert.get("priority", "high"),
                ),
            }
        )

    return enriched


def _action_for_alert(alert: dict) -> str:
    if alert.get("reason") == "new_market_entry":
        return "Evaluate routing 20-40% of eligible traffic to this model"
    drop = abs(float(alert.get("pct_change", 0.0)))
    if drop >= 25:
        return "Shift 40-60% of traffic after validation run"
    return "Shift 20-40% of traffic and monitor quality"


def append_alert_history(alerts: list[dict]) -> None:
    history = _load_json(ALERTS_LOG_PATH, default={"alerts": []})
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    for alert in alerts:
        history["alerts"].append(
            {
                "timestamp": timestamp,
                "model_id": alert["model_id"],
                "workload_id": alert["workload_id"],
                "priority": alert.get("priority"),
                "reason": alert.get("reason"),
                "verified": False,
                "cyclical": False,
            }
        )
    _save_json(ALERTS_LOG_PATH, history)


def run_price_hunter(*, dry_run: bool = False) -> dict[str, Any]:
    """Fetch prices, update baselines, scan for alerts, and return a summary."""
    rules = _load_json(THRESHOLDS_PATH, default={})
    workloads_payload = _load_json(WORKLOADS_PATH, default={"workloads": []})
    workloads = workloads_payload.get("workloads", [])

    snapshot = fetch_prices()
    write_prices(snapshot)
    rows_recorded = record_snapshot(snapshot)
    log.info("Recorded %d price snapshot row(s) to SQLite", rows_recorded)

    baselines = _load_json(BASELINES_PATH, default={"snapshots": [], "model_ids": []})
    baselines = update_baselines(snapshot, baselines)
    _save_json(BASELINES_PATH, baselines)

    alerts = scan_for_alerts(
        snapshot.get("models", []),
        baselines,
        workloads,
        rules,
    )
    alerts = enrich_alerts(alerts, snapshot.get("models", []), workloads)

    slack_delivery: dict[str, Any] = {
        "delivered": 0,
        "skipped": 0,
        "failed": 0,
        "dry_run": dry_run,
    }

    if alerts:
        append_alert_history(alerts)
        record_alert_events(alerts, snapshot["fetched_at"])
        log.info("Generated %d alert(s)", len(alerts))
        slack_delivery = deliver_slack_alerts(alerts, dry_run=dry_run)
    else:
        log.info("No alerts triggered")

    return {
        "status": "ok",
        "fetched_at": snapshot["fetched_at"],
        "model_count": snapshot["model_count"],
        "alert_count": len(alerts),
        "slack_delivery": slack_delivery,
        "alerts": alerts,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Price Drop Hunter (Routine 1)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print Slack alert blocks without posting to Slack",
    )
    args = parser.parse_args(argv)

    output = run_price_hunter(dry_run=args.dry_run)
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
