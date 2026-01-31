-- Create slack_messages table
CREATE TABLE slack_messages (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id text NOT NULL,
  channel_id text NOT NULL,
  text text,
  timestamp text NOT NULL,
  raw_event jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Create indexes
CREATE INDEX slack_messages_user_id_idx ON slack_messages (user_id);
CREATE INDEX slack_messages_channel_id_idx ON slack_messages (channel_id);
CREATE INDEX slack_messages_timestamp_idx ON slack_messages (timestamp);
CREATE INDEX slack_messages_created_at_idx ON slack_messages (created_at);

-- Enable Row Level Security
ALTER TABLE slack_messages ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Allow authenticated users to read all messages
CREATE POLICY "Allow authenticated users to read slack messages"
  ON slack_messages FOR SELECT
  TO authenticated
  USING (true);

-- Allow service role to insert messages
CREATE POLICY "Allow service role to insert slack messages"
  ON slack_messages FOR INSERT
  TO service_role
  WITH CHECK (true);

-- Allow service role to update messages
CREATE POLICY "Allow service role to update slack messages"
  ON slack_messages FOR UPDATE
  TO service_role
  USING (true);
