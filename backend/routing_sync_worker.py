"""Sync routing recommendations to Supabase."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.engine.generate_routing_config import build_routing_config  # noqa: E402
from backend.engine.supabase_sync import get_supabase_client, sync_routing_recommendations  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format='{"level":"%(levelname)s","message":"%(message)s","ts":"%(asctime)s"}',
)
log = logging.getLogger(__name__)


def main() -> int:
    config = build_routing_config()
    client = get_supabase_client()
    if client is None:
        print(json.dumps({"status": "ok", "routes": len(config.get("routes", [])), "synced": 0}))
        return 0
    count = sync_routing_recommendations(client, config)
    log.info("Synced %d routing recommendations", count)
    print(json.dumps({"status": "ok", "routes": len(config.get("routes", [])), "synced": count}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
