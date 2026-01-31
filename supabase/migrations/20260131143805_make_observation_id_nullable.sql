-- Make observation_id nullable in labeled_actions for testing purposes

ALTER TABLE labeled_actions ALTER COLUMN observation_id DROP NOT NULL;
