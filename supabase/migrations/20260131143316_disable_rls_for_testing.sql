-- Disable RLS for development and testing
-- WARNING: This should only be used in development environment

-- Disable RLS on existing tables (use IF EXISTS for safety)
DO $$ 
BEGIN
  -- System Layer
  IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'sessions') THEN
    ALTER TABLE sessions DISABLE ROW LEVEL SECURITY;
  END IF;
  
  IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'users') THEN
    ALTER TABLE users DISABLE ROW LEVEL SECURITY;
  END IF;
  
  IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'configs') THEN
    ALTER TABLE configs DISABLE ROW LEVEL SECURITY;
  END IF;
  
  -- Raw Data Layer
  IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'screenshots') THEN
    ALTER TABLE screenshots DISABLE ROW LEVEL SECURITY;
  END IF;
  
  IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'input_events') THEN
    ALTER TABLE input_events DISABLE ROW LEVEL SECURITY;
  END IF;
  
  IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'observations') THEN
    ALTER TABLE observations DISABLE ROW LEVEL SECURITY;
  END IF;
  
  -- Analysis Layer
  IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'labeled_actions') THEN
    ALTER TABLE labeled_actions DISABLE ROW LEVEL SECURITY;
  END IF;
  
  IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'session_sequences') THEN
    ALTER TABLE session_sequences DISABLE ROW LEVEL SECURITY;
  END IF;
  
  -- Pattern Layer
  IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'detected_patterns') THEN
    ALTER TABLE detected_patterns DISABLE ROW LEVEL SECURITY;
  END IF;
  
  -- HITL Layer
  IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'interpreted_answers') THEN
    ALTER TABLE interpreted_answers DISABLE ROW LEVEL SECURITY;
  END IF;
  
  -- Spec Layer
  IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'agent_specs') THEN
    ALTER TABLE agent_specs DISABLE ROW LEVEL SECURITY;
  END IF;
  
  IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'spec_history') THEN
    ALTER TABLE spec_history DISABLE ROW LEVEL SECURITY;
  END IF;
END $$;
