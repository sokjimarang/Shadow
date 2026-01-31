-- Raw Data Layer tables
-- screenshots, input_events, observations

-- Screenshots table
CREATE TABLE screenshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  timestamp TIMESTAMPTZ NOT NULL,
  type TEXT NOT NULL,
  data TEXT NOT NULL,
  thumbnail TEXT NOT NULL,
  resolution JSONB NOT NULL,
  trigger_event_id UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Type constraint
ALTER TABLE screenshots
ADD CONSTRAINT screenshots_type_check
CHECK (type IN ('before', 'after'));

-- Indexes
CREATE INDEX screenshots_session_id_idx ON screenshots(session_id);
CREATE INDEX screenshots_timestamp_idx ON screenshots(timestamp);
CREATE INDEX screenshots_type_idx ON screenshots(type);

-- InputEvents table
CREATE TABLE input_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  timestamp TIMESTAMPTZ NOT NULL,
  type TEXT NOT NULL,
  position JSONB,
  button TEXT,
  click_type TEXT,
  key TEXT,
  modifiers TEXT[],
  active_window JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Type constraint
ALTER TABLE input_events
ADD CONSTRAINT input_events_type_check
CHECK (type IN ('mouse_click', 'mouse_move', 'key_press', 'key_release', 'scroll'));

-- Indexes
CREATE INDEX input_events_session_id_idx ON input_events(session_id);
CREATE INDEX input_events_timestamp_idx ON input_events(timestamp);
CREATE INDEX input_events_type_idx ON input_events(type);

-- Observations table (links screenshots and events)
CREATE TABLE observations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  timestamp TIMESTAMPTZ NOT NULL,
  before_screenshot_id UUID NOT NULL REFERENCES screenshots(id) ON DELETE CASCADE,
  after_screenshot_id UUID NOT NULL REFERENCES screenshots(id) ON DELETE CASCADE,
  event_id UUID NOT NULL REFERENCES input_events(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX observations_session_id_idx ON observations(session_id);
CREATE INDEX observations_timestamp_idx ON observations(timestamp);
CREATE INDEX observations_before_screenshot_id_idx ON observations(before_screenshot_id);
CREATE INDEX observations_after_screenshot_id_idx ON observations(after_screenshot_id);
CREATE INDEX observations_event_id_idx ON observations(event_id);
