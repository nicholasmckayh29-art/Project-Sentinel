-- Pricing Sentinel — initial schema
-- Run via Supabase SQL editor or: supabase db push

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------------------------------------------------------------------------
-- Catalog
-- ---------------------------------------------------------------------------

CREATE TABLE providers (
    id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE models (
    id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL REFERENCES providers(id) ON DELETE CASCADE,
    display_name TEXT NOT NULL,
    pricing JSONB NOT NULL DEFAULT '{}',
    capabilities JSONB NOT NULL DEFAULT '{}',
    limits JSONB NOT NULL DEFAULT '{}',
    benchmarks JSONB NOT NULL DEFAULT '{}',
    metadata JSONB NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE workloads (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    workload_type TEXT NOT NULL,
    characteristics JSONB NOT NULL DEFAULT '{}',
    tier TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE model_capabilities (
    model_id TEXT PRIMARY KEY REFERENCES models(id) ON DELETE CASCADE,
    benchmarks JSONB NOT NULL DEFAULT '{}',
    efficiency_ratio REAL NOT NULL DEFAULT 1.0,
    source TEXT NOT NULL DEFAULT 'inferred'
);

-- ---------------------------------------------------------------------------
-- Time series + alerts
-- ---------------------------------------------------------------------------

CREATE TABLE price_snapshots (
    id BIGSERIAL PRIMARY KEY,
    fetched_at TIMESTAMPTZ NOT NULL,
    model_id TEXT NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    provider_id TEXT NOT NULL REFERENCES providers(id),
    input_per_1m REAL NOT NULL,
    output_per_1m REAL NOT NULL,
    source TEXT NOT NULL DEFAULT 'pricetoken.ai'
);

CREATE INDEX idx_price_snapshots_model_time ON price_snapshots(model_id, fetched_at DESC);
CREATE INDEX idx_price_snapshots_fetched ON price_snapshots(fetched_at DESC);

CREATE TABLE baselines (
    model_id TEXT PRIMARY KEY REFERENCES models(id) ON DELETE CASCADE,
    captured_at TIMESTAMPTZ NOT NULL,
    pricing JSONB NOT NULL,
    benchmarks JSONB NOT NULL DEFAULT '{}',
    capabilities JSONB NOT NULL DEFAULT '{}',
    metadata JSONB NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE market_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    summary TEXT,
    event_type TEXT NOT NULL DEFAULT 'news',
    source TEXT,
    url TEXT,
    published_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_market_events_published ON market_events(published_at DESC);

CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    model_id TEXT NOT NULL REFERENCES models(id),
    workload_id TEXT REFERENCES workloads(id),
    direction TEXT NOT NULL CHECK (direction IN ('drop', 'increase')),
    priority TEXT NOT NULL DEFAULT 'high',
    reason TEXT NOT NULL,
    pct_change REAL,
    true_cost REAL,
    baseline_true_cost REAL,
    quality_delta_pct REAL,
    savings_vs_leader_pct REAL,
    leader_model_id TEXT,
    display_name TEXT,
    workload_name TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_alerts_created ON alerts(created_at DESC);
CREATE INDEX idx_alerts_model ON alerts(model_id, created_at DESC);

-- ---------------------------------------------------------------------------
-- Users
-- ---------------------------------------------------------------------------

CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name TEXT,
    onboarding_complete BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    source TEXT NOT NULL DEFAULT 'stripe' CHECK (source IN ('stripe', 'apple')),
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    status TEXT NOT NULL DEFAULT 'inactive',
    product_id TEXT,
    current_period_end TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id)
);

CREATE TABLE notification_prefs (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email_alerts BOOLEAN NOT NULL DEFAULT true,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_watchlist_models (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    model_id TEXT NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, model_id)
);

CREATE TABLE user_watchlist_providers (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    provider_id TEXT NOT NULL REFERENCES providers(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, provider_id)
);

CREATE TABLE user_watchlist_workloads (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    workload_id TEXT NOT NULL REFERENCES workloads(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, workload_id)
);

-- ---------------------------------------------------------------------------
-- Helpers
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION is_premium(uid UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1 FROM subscriptions s
        WHERE s.user_id = uid
          AND s.status = 'active'
          AND (s.current_period_end IS NULL OR s.current_period_end > now())
    );
$$;

CREATE OR REPLACE FUNCTION watchlist_count(uid UUID)
RETURNS INTEGER
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT (
        (SELECT COUNT(*) FROM user_watchlist_models WHERE user_id = uid) +
        (SELECT COUNT(*) FROM user_watchlist_providers WHERE user_id = uid) +
        (SELECT COUNT(*) FROM user_watchlist_workloads WHERE user_id = uid)
    )::INTEGER;
$$;

-- Auto-create profile on signup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO profiles (id) VALUES (NEW.id);
    INSERT INTO notification_prefs (user_id) VALUES (NEW.id);
    RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- ---------------------------------------------------------------------------
-- Row Level Security
-- ---------------------------------------------------------------------------

ALTER TABLE providers ENABLE ROW LEVEL SECURITY;
ALTER TABLE models ENABLE ROW LEVEL SECURITY;
ALTER TABLE workloads ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_capabilities ENABLE ROW LEVEL SECURITY;
ALTER TABLE price_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE baselines ENABLE ROW LEVEL SECURITY;
ALTER TABLE market_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_prefs ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_watchlist_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_watchlist_providers ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_watchlist_workloads ENABLE ROW LEVEL SECURITY;

-- Public catalog read
CREATE POLICY providers_read ON providers FOR SELECT USING (true);
CREATE POLICY models_read ON models FOR SELECT USING (true);
CREATE POLICY workloads_read ON workloads FOR SELECT USING (true);
CREATE POLICY capabilities_read ON model_capabilities FOR SELECT USING (true);
CREATE POLICY market_events_read ON market_events FOR SELECT USING (true);

-- Baselines readable by authenticated users
CREATE POLICY baselines_read ON baselines FOR SELECT TO authenticated USING (true);

-- Price snapshots: free = last 7 days; premium = all
CREATE POLICY snapshots_read ON price_snapshots FOR SELECT TO authenticated
    USING (
        is_premium(auth.uid())
        OR fetched_at > now() - interval '7 days'
    );

-- Alerts: free = delayed 24h; premium = realtime
CREATE POLICY alerts_read ON alerts FOR SELECT TO authenticated
    USING (
        is_premium(auth.uid())
        OR created_at < now() - interval '24 hours'
    );

-- Profiles
CREATE POLICY profiles_select ON profiles FOR SELECT TO authenticated
    USING (id = auth.uid());
CREATE POLICY profiles_update ON profiles FOR UPDATE TO authenticated
    USING (id = auth.uid());

-- Subscriptions: users read own
CREATE POLICY subscriptions_select ON subscriptions FOR SELECT TO authenticated
    USING (user_id = auth.uid());

-- Notification prefs
CREATE POLICY notif_select ON notification_prefs FOR SELECT TO authenticated
    USING (user_id = auth.uid());
CREATE POLICY notif_update ON notification_prefs FOR UPDATE TO authenticated
    USING (user_id = auth.uid());

-- Watchlists: users manage own; free tier max 3 total items
CREATE POLICY watchlist_models_select ON user_watchlist_models FOR SELECT TO authenticated
    USING (user_id = auth.uid());
CREATE POLICY watchlist_models_insert ON user_watchlist_models FOR INSERT TO authenticated
    WITH CHECK (
        user_id = auth.uid()
        AND (is_premium(auth.uid()) OR watchlist_count(auth.uid()) < 3)
    );
CREATE POLICY watchlist_models_delete ON user_watchlist_models FOR DELETE TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY watchlist_providers_select ON user_watchlist_providers FOR SELECT TO authenticated
    USING (user_id = auth.uid());
CREATE POLICY watchlist_providers_insert ON user_watchlist_providers FOR INSERT TO authenticated
    WITH CHECK (
        user_id = auth.uid()
        AND (is_premium(auth.uid()) OR watchlist_count(auth.uid()) < 3)
    );
CREATE POLICY watchlist_providers_delete ON user_watchlist_providers FOR DELETE TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY watchlist_workloads_select ON user_watchlist_workloads FOR SELECT TO authenticated
    USING (user_id = auth.uid());
CREATE POLICY watchlist_workloads_insert ON user_watchlist_workloads FOR INSERT TO authenticated
    WITH CHECK (
        user_id = auth.uid()
        AND (is_premium(auth.uid()) OR watchlist_count(auth.uid()) < 3)
    );
CREATE POLICY watchlist_workloads_delete ON user_watchlist_workloads FOR DELETE TO authenticated
    USING (user_id = auth.uid());

-- Service role bypasses RLS by default in Supabase

-- Realtime for alerts feed
ALTER PUBLICATION supabase_realtime ADD TABLE alerts;
ALTER PUBLICATION supabase_realtime ADD TABLE market_events;
