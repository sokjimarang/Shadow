-- SessionSequence table (Analysis Layer)
-- Action sequences within a session

CREATE TABLE session_sequences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ,
  action_ids UUID[] NOT NULL DEFAULT '{}',
  apps_used TEXT[] NOT NULL DEFAULT '{}',
  action_count INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'recording',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX session_sequences_session_id_idx ON session_sequences(session_id);
CREATE INDEX session_sequences_status_idx ON session_sequences(status);
CREATE INDEX session_sequences_start_time_idx ON session_sequences(start_time);

-- Status constraint
ALTER TABLE session_sequences
ADD CONSTRAINT session_sequences_status_check
CHECK (status IN ('recording', 'completed', 'analyzed'));
