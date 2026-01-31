-- Create slack_interaction_answers table
CREATE TABLE slack_interaction_answers (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id text NOT NULL,
  selected_option text NOT NULL,
  additional_context text,
  create_exception_rule boolean,
  answered_at timestamptz NOT NULL,
  user_id text NOT NULL,
  raw_payload jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Create indexes
CREATE INDEX slack_interaction_answers_session_id_idx ON slack_interaction_answers (session_id);
CREATE INDEX slack_interaction_answers_user_id_idx ON slack_interaction_answers (user_id);
CREATE INDEX slack_interaction_answers_answered_at_idx ON slack_interaction_answers (answered_at);
CREATE INDEX slack_interaction_answers_created_at_idx ON slack_interaction_answers (created_at);

-- Enable Row Level Security
ALTER TABLE slack_interaction_answers ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Allow authenticated users to read all answers
CREATE POLICY "Allow authenticated users to read slack interaction answers"
  ON slack_interaction_answers FOR SELECT
  TO authenticated
  USING (true);

-- Allow service role to insert answers
CREATE POLICY "Allow service role to insert slack interaction answers"
  ON slack_interaction_answers FOR INSERT
  TO service_role
  WITH CHECK (true);

-- Allow service role to update answers
CREATE POLICY "Allow service role to update slack interaction answers"
  ON slack_interaction_answers FOR UPDATE
  TO service_role
  USING (true);
