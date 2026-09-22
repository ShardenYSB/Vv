CREATE TABLE users (
 id BIGSERIAL PRIMARY KEY, telegram_id BIGINT NOT NULL UNIQUE, username TEXT, first_name TEXT,
 referrer_id BIGINT REFERENCES users(id), stars_balance INTEGER NOT NULL DEFAULT 0,
 is_blocked BOOLEAN NOT NULL DEFAULT FALSE, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE referrals (
 id BIGSERIAL PRIMARY KEY, referrer_id BIGINT NOT NULL REFERENCES users(id), referred_id BIGINT NOT NULL UNIQUE REFERENCES users(id),
 status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','confirmed','rejected')), reward INTEGER NOT NULL DEFAULT 0,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), confirmed_at TIMESTAMPTZ, CHECK(referrer_id <> referred_id)
);
CREATE TABLE sponsor_checks (id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES users(id), resource_id TEXT NOT NULL, url TEXT NOT NULL, completed BOOLEAN NOT NULL, checked_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(user_id, resource_id));
CREATE TABLE tasks (id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES users(id), resource_id TEXT NOT NULL, url TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'received', reward INTEGER NOT NULL DEFAULT 0, rewarded BOOLEAN NOT NULL DEFAULT FALSE, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), completed_at TIMESTAMPTZ, UNIQUE(user_id, resource_id));
CREATE TABLE star_transactions (id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES users(id), amount INTEGER NOT NULL, type TEXT NOT NULL CHECK(type IN ('referral','task','admin','withdraw','correction')), source_id TEXT, description TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE INDEX star_transactions_user_created_idx ON star_transactions(user_id, created_at DESC);
