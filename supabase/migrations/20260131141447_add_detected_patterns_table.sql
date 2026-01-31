-- DetectedPattern table (Pattern Layer)
-- Detected patterns with JSONB fields

CREATE TABLE detected_patterns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pattern_id TEXT,
  name TEXT,
  description TEXT,
  core_sequence JSONB NOT NULL DEFAULT '[]'::jsonb,
  apps_involved TEXT[] NOT NULL DEFAULT '{}',
  occurrences INTEGER NOT NULL DEFAULT 0,
  first_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  session_ids UUID[] NOT NULL DEFAULT '{}',
  variations JSONB NOT NULL DEFAULT '[]'::jsonb,
  uncertainties JSONB NOT NULL DEFAULT '[]'::jsonb,
  status TEXT NOT NULL DEFAULT 'detected',
  confidence NUMERIC NOT NULL DEFAULT 1.0,
  spec_id UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX detected_patterns_pattern_id_idx ON detected_patterns(pattern_id);
CREATE INDEX detected_patterns_status_idx ON detected_patterns(status);
CREATE INDEX detected_patterns_first_seen_idx ON detected_patterns(first_seen);
CREATE INDEX detected_patterns_spec_id_idx ON detected_patterns(spec_id);

-- Status constraint
ALTER TABLE detected_patterns
ADD CONSTRAINT detected_patterns_status_check
CHECK (status IN ('detected', 'confirming', 'confirmed', 'rejected'));
