-- PostgreSQL schema for moderation and auditable inline administration.
CREATE TABLE IF NOT EXISTS blocked_resources (
    id BIGSERIAL PRIMARY KEY,
    resource_id TEXT NOT NULL,
    url TEXT NOT NULL,
    reason TEXT,
    blocked_by BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE UNIQUE INDEX IF NOT EXISTS blocked_resources_active_resource_id_idx ON blocked_resources (resource_id) WHERE is_active;

CREATE TABLE IF NOT EXISTS unresolved_resources (
    id BIGSERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    resource_id TEXT,
    user_id BIGINT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'blocked', 'ignored', 'resolved')),
    error_type TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ,
    resolved_by BIGINT
);

CREATE TABLE IF NOT EXISTS admin_logs (
    id BIGSERIAL PRIMARY KEY,
    admin_id BIGINT NOT NULL,
    action TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- bot_settings stores max_op and referral ranges as application-managed key/value rows.
CREATE TABLE IF NOT EXISTS bot_settings (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
