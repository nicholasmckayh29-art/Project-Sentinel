"""Market sync worker: news ingest, equity quotes, macro, community signals."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.engine.fetch_community import fetch_community_signals  # noqa: E402
from backend.engine.fetch_equity_quotes import fetch_equity_quotes  # noqa: E402
from backend.engine.fetch_macro import fetch_macro_snapshots  # noqa: E402
from backend.engine.ingest_news import ingest_all  # noqa: E402
from backend.engine.supabase_sync import (  # noqa: E402
    get_supabase_client,
    sync_community_signals,
    sync_macro_snapshots,
    sync_market_events,
    sync_market_quotes,
)

logging.basicConfig(
    level=logging.INFO,
    format='{"level":"%(levelname)s","message":"%(message)s","ts":"%(asctime)s"}',
)
log = logging.getLogger(__name__)


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    stats: dict[str, int] = {}

    events = ingest_all(enrich_og=not dry_run)
    quotes = fetch_equity_quotes()
    macro = fetch_macro_snapshots()
    community = fetch_community_signals()

    stats["events_collected"] = len(events)
    stats["quotes_collected"] = len(quotes)
    stats["macro_collected"] = len(macro)
    stats["community_collected"] = len(community)

    client = get_supabase_client()
    if client is None:
        log.warning("Supabase not configured — dry output only")
        print(json.dumps({"status": "ok", "dry_run": True, **stats}))
        return 0

    if not dry_run:
        stats["events_synced"] = sync_market_events(client, events)
        stats["quotes_synced"] = sync_market_quotes(client, quotes)
        stats["macro_synced"] = sync_macro_snapshots(client, macro)
        stats["community_synced"] = sync_community_signals(client, community)

    log.info("Market sync complete: %s", stats)
    print(json.dumps({"status": "ok", **stats}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
