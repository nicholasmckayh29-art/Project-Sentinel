#!/usr/bin/env python3
"""Seed Supabase catalog from local JSON files."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.engine.supabase_sync import (  # noqa: E402
    get_supabase_client,
    normalize_supabase_url,
    sync_catalog,
    sync_workloads,
)

DATA = ROOT / "data"
TABLES = ("workloads", "providers", "models", "model_capabilities")


def _count(client, table: str) -> int:
    result = client.table(table).select("*", count="exact").limit(0).execute()
    return int(result.count or 0)


def main() -> int:
    raw_url = os.environ.get("SUPABASE_URL", "")
    try:
        client = get_supabase_client()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if client is None:
        print(
            "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY\n"
            "  SUPABASE_URL=https://YOUR-PROJECT-REF.supabase.co\n"
            "  (from Supabase → Project Settings → API → Project URL)",
            file=sys.stderr,
        )
        return 1

    print(f"Seeding {normalize_supabase_url(raw_url)} ...")

    prices = json.loads((DATA / "current_prices.json").read_text())
    workloads = json.loads((DATA / "workloads.json").read_text())
    model_count = len(prices.get("models", []))
    workload_count = len(workloads.get("workloads", []))

    try:
        sync_workloads(client, workloads.get("workloads", []))
        sync_catalog(client, prices.get("models", []))
    except Exception as exc:
        print(f"Seed failed: {exc}", file=sys.stderr)
        print(
            "\nIf you see 'relation does not exist' or schema errors, run\n"
            "  supabase/migrations/001_initial_schema.sql\n"
            "in Supabase → SQL Editor first.",
            file=sys.stderr,
        )
        return 1

    print(f"Seeded {model_count} models and {workload_count} workloads")
    print("\nVerified row counts:")
    for table in TABLES:
        print(f"  {table}: {_count(client, table)}")

    models_in_db = _count(client, "models")
    if models_in_db == 0:
        print(
            "\nERROR: seed reported success but models table is empty.\n"
            "Check you are viewing project eamkkmlpphsimvznjjcf → Table Editor → public → models",
            file=sys.stderr,
        )
        return 1

    print(f"\nDone. Open Table Editor → schema 'public' → table 'models' ({models_in_db} rows).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
