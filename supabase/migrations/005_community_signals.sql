-- Community & labor signals (HF trending, AI jobs, etc.)

CREATE TABLE community_signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    signal_type TEXT NOT NULL,
    label TEXT NOT NULL,
    value REAL,
    metadata JSONB NOT NULL DEFAULT '{}',
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_community_signals_type ON community_signals(signal_type, fetched_at DESC);

ALTER TABLE community_signals ENABLE ROW LEVEL SECURITY;
CREATE POLICY community_signals_read ON community_signals FOR SELECT USING (true);
