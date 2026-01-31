-- Update sessions table to match data_schema.md

-- Add observation_count column
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS observation_count INTEGER NOT NULL DEFAULT 0;

-- Rename columns to match schema
ALTER TABLE sessions RENAME COLUMN started_at TO start_time;
ALTER TABLE sessions RENAME COLUMN completed_at TO end_time;

-- Drop unused columns
ALTER TABLE sessions DROP COLUMN IF EXISTS duration;
ALTER TABLE sessions DROP COLUMN IF EXISTS frame_count;

-- Update status constraint to match SessionStatus enum
ALTER TABLE sessions DROP CONSTRAINT IF EXISTS sessions_status_check;
ALTER TABLE sessions ADD CONSTRAINT sessions_status_check 
  CHECK (status IN ('active', 'paused', 'completed'));

-- Update default status
ALTER TABLE sessions ALTER COLUMN status SET DEFAULT 'active';
