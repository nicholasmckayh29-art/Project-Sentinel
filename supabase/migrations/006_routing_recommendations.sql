-- Persist routing recommendations from generate_routing_config

CREATE TABLE routing_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workload_id TEXT NOT NULL REFERENCES workloads(id) ON DELETE CASCADE,
    models JSONB NOT NULL DEFAULT '[]',
    projections JSONB NOT NULL DEFAULT '{}',
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_routing_workload ON routing_recommendations(workload_id, generated_at DESC);

ALTER TABLE routing_recommendations ENABLE ROW LEVEL SECURITY;
CREATE POLICY routing_read ON routing_recommendations FOR SELECT USING (true);
