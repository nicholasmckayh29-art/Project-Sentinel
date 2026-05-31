-- Market terminal: equity quotes + market_events dedupe

CREATE TABLE market_quotes (
    symbol TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL,
    change_pct REAL,
    fetched_at TIMESTAMPTZ NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_market_quotes_fetched ON market_quotes(fetched_at DESC);

ALTER TABLE market_events ADD COLUMN IF NOT EXISTS url_hash TEXT;
ALTER TABLE market_events DROP CONSTRAINT IF EXISTS market_events_url_hash_key;
ALTER TABLE market_events ADD CONSTRAINT market_events_url_hash_key UNIQUE (url_hash);

ALTER TABLE market_quotes ENABLE ROW LEVEL SECURITY;
CREATE POLICY market_quotes_read ON market_quotes FOR SELECT USING (true);

ALTER PUBLICATION supabase_realtime ADD TABLE market_quotes;
