"""Verify Supabase connection and row counts."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.engine.supabase_sync import get_supabase_client, normalize_supabase_url  # noqa: E402

TABLES = ("workloads", "providers", "models", "model_capabilities", "alerts", "price_snapshots")


def count_rows(client, table: str) -> int | None:
    try:
        result = client.table(table).select("*", count="exact").limit(0).execute()
        return result.count
    except Exception as exc:
        print(f"  {table}: ERROR — {exc}", file=sys.stderr)
        return None


def main() -> int:
    raw_url = os.environ.get("SUPABASE_URL", "")
    if not raw_url:
        print("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY", file=sys.stderr)
        return 1

    print(f"Project URL: {normalize_supabase_url(raw_url)}")
    print(f"Service key set: {'yes' if os.environ.get('SUPABASE_SERVICE_ROLE_KEY') else 'NO — required'}")

    try:
        client = get_supabase_client()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if client is None:
        print("Missing SUPABASE_SERVICE_ROLE_KEY", file=sys.stderr)
        return 1

    print("\nRow counts (public schema):")
    ok = True
    for table in TABLES:
        n = count_rows(client, table)
        if n is None:
            ok = False
            print(f"  {table}: (table missing or inaccessible — run migration SQL?)")
        else:
            print(f"  {table}: {n}")
            if table == "models" and n == 0:
                ok = False

    if not ok:
        print(
            "\nIf counts are 0 or tables missing:\n"
            "  1. Run supabase/migrations/001_initial_schema.sql in SQL Editor\n"
            "  2. Re-run: python backend/engine/seed_supabase.py\n"
            "  3. In Table Editor, select schema 'public' and table 'models' (not auth.users)",
            file=sys.stderr,
        )
        return 1

    print("\nOK — data is in Supabase.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
