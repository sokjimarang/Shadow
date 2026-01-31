-- Shadow AI Database Initial Schema

-- Sessions table: Stores recording session information
CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT,
  duration NUMERIC NOT NULL DEFAULT 0,
  frame_count INTEGER NOT NULL DEFAULT 0,
  event_count INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'pending',
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create index for sessions
CREATE INDEX sessions_user_id_idx ON sessions(user_id);
CREATE INDEX sessions_status_idx ON sessions(status);
CREATE INDEX sessions_created_at_idx ON sessions(created_at DESC);

-- Analysis results table: Stores AI analysis results
CREATE TABLE analysis_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  action_type TEXT NOT NULL,
  target TEXT NOT NULL,
  context TEXT,
  description TEXT,
  confidence NUMERIC,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for analysis_results
CREATE INDEX analysis_results_session_id_idx ON analysis_results(session_id);
CREATE INDEX analysis_results_action_type_idx ON analysis_results(action_type);
CREATE INDEX analysis_results_created_at_idx ON analysis_results(created_at DESC);

-- Patterns table: Stores detected patterns
CREATE TABLE patterns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  pattern_type TEXT NOT NULL DEFAULT 'sequence',
  count INTEGER NOT NULL DEFAULT 0,
  actions JSONB NOT NULL DEFAULT '[]'::jsonb,
  similarity_score NUMERIC,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for patterns
CREATE INDEX patterns_session_id_idx ON patterns(session_id);
CREATE INDEX patterns_pattern_type_idx ON patterns(pattern_type);
CREATE INDEX patterns_created_at_idx ON patterns(created_at DESC);

-- Slack events table: Stores Slack event logs
CREATE TABLE slack_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type TEXT NOT NULL,
  user_id TEXT,
  channel_id TEXT,
  payload JSONB NOT NULL,
  processed BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for slack_events
CREATE INDEX slack_events_event_type_idx ON slack_events(event_type);
CREATE INDEX slack_events_user_id_idx ON slack_events(user_id);
CREATE INDEX slack_events_processed_idx ON slack_events(processed);
CREATE INDEX slack_events_created_at_idx ON slack_events(created_at DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE slack_events ENABLE ROW LEVEL SECURITY;

-- RLS Policies for sessions
CREATE POLICY "Users can view their own sessions"
  ON sessions FOR SELECT
  USING (auth.uid()::text = user_id OR user_id IS NULL);

CREATE POLICY "Users can insert their own sessions"
  ON sessions FOR INSERT
  WITH CHECK (auth.uid()::text = user_id OR user_id IS NULL);

CREATE POLICY "Users can update their own sessions"
  ON sessions FOR UPDATE
  USING (auth.uid()::text = user_id OR user_id IS NULL);

-- RLS Policies for analysis_results
CREATE POLICY "Users can view analysis results for their sessions"
  ON analysis_results FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM sessions
      WHERE sessions.id = analysis_results.session_id
      AND (sessions.user_id = auth.uid()::text OR sessions.user_id IS NULL)
    )
  );

CREATE POLICY "Users can insert analysis results for their sessions"
  ON analysis_results FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM sessions
      WHERE sessions.id = analysis_results.session_id
      AND (sessions.user_id = auth.uid()::text OR sessions.user_id IS NULL)
    )
  );

-- RLS Policies for patterns
CREATE POLICY "Users can view patterns for their sessions"
  ON patterns FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM sessions
      WHERE sessions.id = patterns.session_id
      AND (sessions.user_id = auth.uid()::text OR sessions.user_id IS NULL)
    )
  );

CREATE POLICY "Users can insert patterns for their sessions"
  ON patterns FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM sessions
      WHERE sessions.id = patterns.session_id
      AND (sessions.user_id = auth.uid()::text OR sessions.user_id IS NULL)
    )
  );

-- RLS Policies for slack_events (public read for now, can be restricted later)
CREATE POLICY "Anyone can view slack events"
  ON slack_events FOR SELECT
  USING (true);

CREATE POLICY "Service can insert slack events"
  ON slack_events FOR INSERT
  WITH CHECK (true);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
CREATE TRIGGER update_sessions_updated_at
  BEFORE UPDATE ON sessions
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE sessions IS 'Stores recording session information from shadow-py';
COMMENT ON TABLE analysis_results IS 'Stores AI analysis results (Claude/Gemini) for each session';
COMMENT ON TABLE patterns IS 'Stores detected repetitive patterns';
COMMENT ON TABLE slack_events IS 'Stores Slack bot event logs';
