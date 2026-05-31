-- Macro context strip (FRED / Econdb)

CREATE TABLE macro_snapshots (
    series_id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    value REAL,
    change_pct REAL,
    fetched_at TIMESTAMPTZ NOT NULL
);

ALTER TABLE macro_snapshots ENABLE ROW LEVEL SECURITY;
CREATE POLICY macro_snapshots_read ON macro_snapshots FOR SELECT USING (true);
