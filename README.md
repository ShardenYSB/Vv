# OP Bot

Aiogram 3 Telegram bot foundation for BotoHub mandatory subscriptions and tasks, referral rewards, internal Stars ledger, and moderation.

## Run
1. Create the local configuration: `cp .env.example .env`.
2. Open `.env` and replace every `CHANGE_ME...` value. `BOT_TOKEN` comes from **@BotFather**; `BOTOHUB_TOKEN` comes from BotoHub; `ADMIN_IDS` is your own numeric Telegram user ID. **Do not enter a bot ID**—Telegram determines it from `BOT_TOKEN`.
3. `POSTGRES_PASSWORD` and the password embedded in `DATABASE_URL` must be identical.
4. Start dependencies and apply all idempotent migrations: `docker compose up -d postgres redis && docker compose run --rm migrate`.
5. Build and start the bot: `docker compose up -d --build telegram-bot`.

Only `/start` is a command. All user navigation uses inline callback buttons; sponsor/task resource buttons use URL buttons as required to open the BotoHub-provided target. “Stars” are internal ledger credits, not a transfer of real Telegram XTR.

## Configuration

The checked-in `.env.example` documents every required value. The real `.env` is ignored by Git. The application deliberately refuses placeholder values and invalid `MAX_OP`/`ADMIN_IDS` settings at startup rather than connecting with broken configuration.
