"""Simulate a price-drop alert by inflating baselines for demo purposes."""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.alerts.slack_formatter import format_price_alert  # noqa: E402
from backend.engine.fetch_prices import apply_capability_overrides  # noqa: E402
from backend.engine.run_price_hunter import enrich_alerts  # noqa: E402
from backend.engine.validate_alerts import scan_for_alerts  # noqa: E402

DATA_DIR = ROOT / "data"
CONFIG_DIR = ROOT / "config"


def _load_json(path: Path, default: dict | list | None = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    with path.open() as handle:
        return json.load(handle)


def inflate_baseline_for_model(
    baselines: dict[str, Any],
    model_id: str,
    *,
    inflate_factor: float = 2.0,
) -> dict[str, Any]:
    """Return baselines with inflated output pricing for one model (in-memory copy)."""
    demo = deepcopy(baselines)
    for snapshot in demo.get("snapshots", []):
        if snapshot.get("model_id") != model_id:
            continue
        pricing = snapshot.setdefault("pricing", {})
        output = float(pricing.get("output_per_1m", 0.0))
        if output > 0:
            pricing["output_per_1m"] = round(output * inflate_factor, 6)
        input_price = float(pricing.get("input_per_1m", 0.0))
        if input_price > 0:
            pricing["input_per_1m"] = round(input_price * inflate_factor, 6)
        break
    else:
        raise ValueError(f"Model {model_id!r} not found in baselines snapshots")
    return demo


def run_demo_alert(
    *,
    model_id: str,
    inflate_factor: float = 2.0,
    prices_path: Path = DATA_DIR / "current_prices.json",
    baselines_path: Path = DATA_DIR / "baselines.json",
    workloads_path: Path = DATA_DIR / "workloads.json",
    rules_path: Path = CONFIG_DIR / "threshold_rules.json",
) -> dict[str, Any]:
    """Build demo baselines, scan for alerts, and return enriched alert payload."""
    prices = _load_json(prices_path)
    baselines = _load_json(baselines_path, default={"snapshots": [], "model_ids": []})
    workloads = _load_json(workloads_path, default={"workloads": []}).get("workloads", [])
    rules = _load_json(rules_path, default={})

    models = apply_capability_overrides(prices.get("models", []))
    demo_baselines = inflate_baseline_for_model(baselines, model_id, inflate_factor=inflate_factor)

    alerts = scan_for_alerts(models, demo_baselines, workloads, rules)
    alerts = enrich_alerts(alerts, models, workloads)
    model_alerts = [alert for alert in alerts if alert.get("model_id") == model_id]

    return {
        "status": "ok",
        "demo_model_id": model_id,
        "inflate_factor": inflate_factor,
        "alert_count": len(model_alerts),
        "alerts": model_alerts,
    }


def _format_slack_preview(blocks: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for block in blocks:
        block_type = block.get("type")
        if block_type == "header":
            lines.append(block["text"]["text"])
        elif block_type == "section":
            text = block.get("text", {})
            if text.get("type") == "mrkdwn":
                lines.append(text["text"].replace("\n", " | "))
            for field in block.get("fields", []):
                lines.append(field["text"].replace("*", ""))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model-id",
        default="claude-haiku-4-5-20251001",
        help="Model whose baseline output price is inflated for the demo",
    )
    parser.add_argument(
        "--inflate-factor",
        type=float,
        default=2.0,
        help="Multiply baseline input/output per-1M rates (default: 2.0 → ~50%% drop)",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Print JSON only (no Slack preview lines)",
    )
    args = parser.parse_args(argv)

    try:
        result = run_demo_alert(model_id=args.model_id, inflate_factor=args.inflate_factor)
    except ValueError as exc:
        print(json.dumps({"status": "error", "message": str(exc)}))
        return 1

    if not args.json_only:
        print(f"Demo price alert for {args.model_id} (baseline ×{args.inflate_factor})")
        print(f"Alerts triggered: {result['alert_count']}\n")
        for alert in result["alerts"]:
            print(f"— {alert.get('workload_name')} ({alert.get('priority')}, {alert.get('reason')})")
            print(f"  True cost drop: {alert.get('pct_change')}%")
            blocks = alert.get("slack_blocks", [])
            if blocks:
                print("  Slack preview:")
                for line in _format_slack_preview(blocks).split("\n"):
                    print(f"    {line}")
            print()

    print(json.dumps(result, indent=2))
    return 0 if result["alert_count"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
