-- HITL and Spec tables migration
-- Creates: agent_specs, spec_history, hitl_questions, hitl_answers

-- ==================================================
-- 1. agent_specs table
-- ==================================================

CREATE TABLE IF NOT EXISTS agent_specs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pattern_id TEXT NOT NULL,
  version TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft',
  content JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS agent_specs_pattern_id_idx ON agent_specs(pattern_id);
CREATE INDEX IF NOT EXISTS agent_specs_status_idx ON agent_specs(status);
CREATE INDEX IF NOT EXISTS agent_specs_updated_at_idx ON agent_specs(updated_at DESC);

-- Status constraint
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'agent_specs_status_check'
  ) THEN
    ALTER TABLE agent_specs
    ADD CONSTRAINT agent_specs_status_check
    CHECK (status IN ('draft', 'active', 'archived'));
  END IF;
END $$;

-- ==================================================
-- 2. spec_history table
-- ==================================================

CREATE TABLE IF NOT EXISTS spec_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  spec_id UUID NOT NULL REFERENCES agent_specs(id) ON DELETE CASCADE,
  version TEXT NOT NULL,
  previous_version TEXT,
  change_type TEXT NOT NULL,
  change_summary TEXT NOT NULL,
  changes JSONB NOT NULL DEFAULT '[]'::jsonb,
  source TEXT NOT NULL,
  source_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS spec_history_spec_id_idx ON spec_history(spec_id);
CREATE INDEX IF NOT EXISTS spec_history_created_at_idx ON spec_history(created_at DESC);

-- Constraints
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'spec_history_change_type_check'
  ) THEN
    ALTER TABLE spec_history
    ADD CONSTRAINT spec_history_change_type_check
    CHECK (change_type IN ('create', 'update', 'delete'));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'spec_history_source_check'
  ) THEN
    ALTER TABLE spec_history
    ADD CONSTRAINT spec_history_source_check
    CHECK (source IN ('pattern_detection', 'hitl_answer', 'manual', 'api'));
  END IF;
END $$;

-- ==================================================
-- 3. hitl_questions table
-- ==================================================

CREATE TABLE IF NOT EXISTS hitl_questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pattern_id TEXT NOT NULL,
  uncertainty_id TEXT,
  type TEXT NOT NULL,
  question_text TEXT NOT NULL,
  context TEXT,
  options JSONB NOT NULL DEFAULT '[]'::jsonb,
  allows_freetext BOOLEAN NOT NULL DEFAULT FALSE,
  priority INTEGER NOT NULL DEFAULT 3,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  sent_at TIMESTAMPTZ,
  answered_at TIMESTAMPTZ,
  slack_message_ts TEXT
);

-- Indexes
CREATE INDEX IF NOT EXISTS hitl_questions_pattern_id_idx ON hitl_questions(pattern_id);
CREATE INDEX IF NOT EXISTS hitl_questions_status_idx ON hitl_questions(status);
CREATE INDEX IF NOT EXISTS hitl_questions_priority_idx ON hitl_questions(priority DESC);

-- Constraints
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'hitl_questions_type_check'
  ) THEN
    ALTER TABLE hitl_questions
    ADD CONSTRAINT hitl_questions_type_check
    CHECK (type IN ('anomaly', 'alternative', 'hypothesis', 'quality'));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'hitl_questions_status_check'
  ) THEN
    ALTER TABLE hitl_questions
    ADD CONSTRAINT hitl_questions_status_check
    CHECK (status IN ('pending', 'sent', 'answered', 'expired'));
  END IF;
END $$;

-- ==================================================
-- 4. hitl_answers table
-- ==================================================

CREATE TABLE IF NOT EXISTS hitl_answers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  question_id UUID NOT NULL REFERENCES hitl_questions(id) ON DELETE CASCADE,
  user_id TEXT NOT NULL,
  response_type TEXT NOT NULL,
  selected_option_id TEXT,
  freetext TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS hitl_answers_question_id_idx ON hitl_answers(question_id);
CREATE INDEX IF NOT EXISTS hitl_answers_user_id_idx ON hitl_answers(user_id);

-- Constraint
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'hitl_answers_response_type_check'
  ) THEN
    ALTER TABLE hitl_answers
    ADD CONSTRAINT hitl_answers_response_type_check
    CHECK (response_type IN ('button', 'freetext'));
  END IF;
END $$;

-- ==================================================
-- 5. Disable RLS for testing
-- ==================================================

ALTER TABLE agent_specs DISABLE ROW LEVEL SECURITY;
ALTER TABLE spec_history DISABLE ROW LEVEL SECURITY;
ALTER TABLE hitl_questions DISABLE ROW LEVEL SECURITY;
ALTER TABLE hitl_answers DISABLE ROW LEVEL SECURITY;
