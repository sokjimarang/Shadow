-- LabeledAction table (Analysis Layer)
-- Labeled actions from VLM analysis

CREATE TABLE labeled_actions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  observation_id UUID REFERENCES observations(id) ON DELETE CASCADE,
  session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
  timestamp TIMESTAMPTZ NOT NULL,
  action_type TEXT NOT NULL,
  target_element TEXT NOT NULL,
  app TEXT NOT NULL,
  app_context TEXT,
  semantic_label TEXT NOT NULL,
  intent_guess TEXT,
  confidence NUMERIC NOT NULL DEFAULT 1.0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX labeled_actions_session_id_idx ON labeled_actions(session_id);
CREATE INDEX labeled_actions_observation_id_idx ON labeled_actions(observation_id);
CREATE INDEX labeled_actions_timestamp_idx ON labeled_actions(timestamp);
CREATE INDEX labeled_actions_action_type_idx ON labeled_actions(action_type);
