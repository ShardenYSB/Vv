# OP Bot

Aiogram 3 Telegram bot foundation for BotoHub mandatory subscriptions and tasks, referral rewards, internal Stars ledger, and moderation.

## Run
1. Copy `.env.example` to `.env` and fill in **real secrets** (never commit `.env`).
2. Run `docker compose up -d --build`.
3. Apply `migrations/001_resource_moderation.sql` and `migrations/002_application_schema.sql` to PostgreSQL before serving traffic.

Only `/start` is a command. All user navigation uses inline callback buttons; sponsor/task resource buttons use URL buttons as required to open the BotoHub-provided target. “Stars” are internal ledger credits, not a transfer of real Telegram XTR.
