-- OdabNote Community Shared Mistakes Table
-- Run this in Supabase SQL Editor: https://supabase.com/dashboard/project/yjybafvdoiaywhpyjuqy/sql

CREATE TABLE shared_mistakes (
  id BIGSERIAL PRIMARY KEY,
  keyword TEXT NOT NULL,
  error_pattern TEXT NOT NULL,
  solution TEXT NOT NULL,
  target_model TEXT DEFAULT 'all',
  shared_by TEXT DEFAULT 'anonymous',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE shared_mistakes ENABLE ROW LEVEL SECURITY;

-- Allow anyone with anon key to INSERT (sharing)
CREATE POLICY "Allow anonymous inserts"
  ON shared_mistakes FOR INSERT
  TO anon
  WITH CHECK (true);

-- Allow anyone with anon key to SELECT (syncing)
CREATE POLICY "Allow anonymous reads"
  ON shared_mistakes FOR SELECT
  TO anon
  USING (true);

-- Index for fast model-based queries
CREATE INDEX idx_shared_mistakes_model ON shared_mistakes(target_model);
CREATE INDEX idx_shared_mistakes_keyword ON shared_mistakes(keyword);
