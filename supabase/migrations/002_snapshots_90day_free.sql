-- Extend free-tier price history window so YTD sparklines work after backfill.
-- Run in Supabase SQL editor after 001_initial_schema.sql.

DROP POLICY IF EXISTS snapshots_read ON price_snapshots;

CREATE POLICY snapshots_read ON price_snapshots FOR SELECT TO authenticated
    USING (
        is_premium(auth.uid())
        OR fetched_at > now() - interval '90 days'
    );
