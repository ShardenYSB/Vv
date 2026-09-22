-- Allows one BotoHub resource to be offered again after an unsuccessful/expired attempt.
CREATE UNIQUE INDEX IF NOT EXISTS tasks_rewarded_once_idx
    ON tasks (user_id, resource_id) WHERE rewarded;

CREATE INDEX IF NOT EXISTS tasks_user_active_idx
    ON tasks (user_id, status) WHERE rewarded = FALSE;

ALTER TABLE users ADD COLUMN IF NOT EXISTS sponsors_completed BOOLEAN NOT NULL DEFAULT FALSE;
