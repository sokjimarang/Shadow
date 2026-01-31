-- InterpretedAnswer table (HITL Layer)
-- Interpreted user responses

CREATE TABLE interpreted_answers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  answer_id UUID NOT NULL,
  action TEXT NOT NULL,
  spec_update JSONB,
  confidence NUMERIC NOT NULL DEFAULT 1.0,
  applied BOOLEAN NOT NULL DEFAULT FALSE,
  applied_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX interpreted_answers_answer_id_idx ON interpreted_answers(answer_id);
CREATE INDEX interpreted_answers_applied_idx ON interpreted_answers(applied);
CREATE INDEX interpreted_answers_action_idx ON interpreted_answers(action);

-- Action constraint
ALTER TABLE interpreted_answers
ADD CONSTRAINT interpreted_answers_action_check
CHECK (action IN ('add_rule', 'add_exception', 'set_quality', 'reject', 'needs_clarification'));
