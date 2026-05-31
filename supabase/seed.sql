-- Seed sample market event for news feed demo
INSERT INTO market_events (title, summary, event_type, source, published_at)
VALUES (
  'OpenAI announces GPT-5 pricing tier adjustments',
  'Industry sources indicate upcoming price repositioning for mid-tier models. Monitor gpt-4o-mini baseline.',
  'rumor',
  'release_radar',
  now() - interval '2 hours'
) ON CONFLICT DO NOTHING;
