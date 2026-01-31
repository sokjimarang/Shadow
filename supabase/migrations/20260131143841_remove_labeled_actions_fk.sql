-- Remove foreign key constraints from labeled_actions for testing

ALTER TABLE labeled_actions DROP CONSTRAINT IF EXISTS labeled_actions_observation_id_fkey;
ALTER TABLE labeled_actions DROP CONSTRAINT IF EXISTS labeled_actions_session_id_fkey;
