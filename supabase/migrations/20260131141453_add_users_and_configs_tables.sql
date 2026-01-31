-- Users and Configs tables (System Layer)

-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slack_user_id TEXT NOT NULL UNIQUE,
  slack_channel_id TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  settings JSONB DEFAULT '{}'::jsonb
);

-- Configs table
CREATE TABLE configs (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  excluded_apps TEXT[] DEFAULT '{}',
  capture_interval_ms INTEGER DEFAULT 100,
  min_pattern_occurrences INTEGER DEFAULT 3,
  hitl_max_questions INTEGER DEFAULT 5,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX users_slack_user_id_idx ON users(slack_user_id);
CREATE INDEX users_created_at_idx ON users(created_at);
