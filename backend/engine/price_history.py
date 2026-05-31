"""SQLite storage for daily price snapshots and alert events."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = ROOT / "data" / "price_history.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    model_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    input_per_1m REAL NOT NULL,
    output_per_1m REAL NOT NULL,
    source TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_snapshots_model_timestamp
    ON snapshots(model_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp
    ON snapshots(timestamp);

CREATE TABLE IF NOT EXISTS alert_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    snapshot_id INTEGER,
    model_id TEXT NOT NULL,
    workload_id TEXT,
    priority TEXT,
    reason TEXT,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id)
);

CREATE INDEX IF NOT EXISTS idx_alert_events_model
    ON alert_events(model_id, timestamp);
"""


def connect(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)


def record_snapshot(
    snapshot: dict[str, Any],
    db_path: Path | str = DEFAULT_DB_PATH,
) -> int:
    """Append one row per model from a fetch snapshot. Returns rows inserted."""
    init_db(db_path)
    timestamp = snapshot["fetched_at"]
    source = snapshot.get("source", "unknown")
    rows = [
        (
            timestamp,
            model["model_id"],
            model.get("provider", "unknown"),
            float(model["pricing"]["input_per_1m"]),
            float(model["pricing"]["output_per_1m"]),
            model.get("metadata", {}).get("data_source", source),
        )
        for model in snapshot.get("models", [])
    ]
    if not rows:
        return 0

    with connect(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO snapshots
                (timestamp, model_id, provider, input_per_1m, output_per_1m, source)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
    return len(rows)


def record_alert_events(
    alerts: list[dict[str, Any]],
    snapshot_timestamp: str,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> int:
    """Link alert events to the most recent snapshot rows for each model."""
    if not alerts:
        return 0

    init_db(db_path)
    event_timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    inserted = 0

    with connect(db_path) as conn:
        for alert in alerts:
            row = conn.execute(
                """
                SELECT id FROM snapshots
                WHERE timestamp = ? AND model_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (snapshot_timestamp, alert["model_id"]),
            ).fetchone()
            snapshot_id = row["id"] if row else None
            conn.execute(
                """
                INSERT INTO alert_events
                    (timestamp, snapshot_id, model_id, workload_id, priority, reason)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event_timestamp,
                    snapshot_id,
                    alert["model_id"],
                    alert.get("workload_id"),
                    alert.get("priority"),
                    alert.get("reason"),
                ),
            )
            inserted += 1
        conn.commit()

    return inserted


def list_recent_snapshots(
    limit: int = 10,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> list[dict[str, Any]]:
    """Return distinct fetch runs, newest first."""
    init_db(db_path)
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT timestamp, source, COUNT(*) AS model_count
            FROM snapshots
            GROUP BY timestamp, source
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_price_trend(
    model_id: str,
    days: int = 30,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> list[dict[str, Any]]:
    """Return price history for a model over the last N days."""
    init_db(db_path)
    cutoff = (
        datetime.now(timezone.utc) - timedelta(days=days)
    ).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT timestamp, model_id, provider, input_per_1m, output_per_1m, source
            FROM snapshots
            WHERE model_id = ? AND timestamp >= ?
            ORDER BY timestamp ASC
            """,
            (model_id, cutoff),
        ).fetchall()
    return [dict(row) for row in rows]


def _cmd_list(args: argparse.Namespace) -> int:
    snapshots = list_recent_snapshots(limit=args.limit, db_path=args.db)
    print(json.dumps({"snapshots": snapshots, "count": len(snapshots)}, indent=2))
    return 0


def _cmd_trend(args: argparse.Namespace) -> int:
    trend = get_price_trend(args.model, days=args.days, db_path=args.db)
    print(
        json.dumps(
            {
                "model_id": args.model,
                "days": args.days,
                "points": trend,
                "count": len(trend),
            },
            indent=2,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Query price snapshot history")
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="Path to SQLite database (default: data/price_history.db)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List recent snapshot runs")
    list_parser.add_argument("--limit", type=int, default=10, help="Max runs to return")
    list_parser.set_defaults(func=_cmd_list)

    trend_parser = subparsers.add_parser("trend", help="Price trend for a model")
    trend_parser.add_argument("--model", required=True, help="Model ID")
    trend_parser.add_argument("--days", type=int, default=30, help="Lookback window in days")
    trend_parser.set_defaults(func=_cmd_trend)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
