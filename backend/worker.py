"""Production worker: run price hunter and sync to Supabase + email alerts."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.engine.email_alerts import send_premium_alert_emails  # noqa: E402
from backend.engine.run_price_hunter import _load_json, run_price_hunter  # noqa: E402
from backend.engine.supabase_sync import get_supabase_client, sync_hunter_result  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format='{"level":"%(levelname)s","message":"%(message)s","ts":"%(asctime)s"}',
)
log = logging.getLogger(__name__)

WORKLOADS_PATH = ROOT / "data" / "workloads.json"
BASELINES_PATH = ROOT / "data" / "baselines.json"
CURRENT_PRICES_PATH = ROOT / "data" / "current_prices.json"


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    result = run_price_hunter(dry_run=dry_run)

    client = get_supabase_client()
    if client is None:
        log.warning("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set — skipping Supabase sync")
        print(json.dumps(result, indent=2))
        return 0

    workloads_payload = _load_json(WORKLOADS_PATH, default={"workloads": []})
    baselines = _load_json(BASELINES_PATH, default={"snapshots": [], "model_ids": []})

    snapshot = {
        "fetched_at": result["fetched_at"],
        "source": "pricetoken.ai",
        "model_count": result["model_count"],
        "models": _load_json(CURRENT_PRICES_PATH, default={}).get("models", []),
    }

    sync_stats = sync_hunter_result(
        client,
        snapshot=snapshot,
        baselines=baselines,
        alerts=result.get("alerts", []),
        workloads=workloads_payload.get("workloads", []),
    )
    log.info("Supabase sync: %s", sync_stats)

    if result.get("alerts") and not dry_run:
        sent = send_premium_alert_emails(client, result["alerts"])
        log.info("Sent %d premium alert email(s)", sent)

    output = {**result, "supabase_sync": sync_stats}
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
