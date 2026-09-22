"""Runtime configuration, read exclusively from environment variables."""
from __future__ import annotations

from dataclasses import dataclass
from os import environ


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    botohub_token: str
    database_url: str
    redis_url: str | None
    admin_ids: frozenset[int]
    max_op: int = 20

    @classmethod
    def from_env(cls) -> "Settings":
        required_names = ("BOT_TOKEN", "BOTOHUB_TOKEN", "DATABASE_URL")
        required = {name: environ.get(name, "").strip() for name in required_names}
        missing = [name for name, value in required.items() if not value or "CHANGE_ME" in value or value == "replace_me"]
        if missing:
            raise RuntimeError("Fill these values in .env before starting: " + ", ".join(missing))

        raw_admin_ids = environ.get("ADMIN_IDS", "").strip()
        try:
            admin_ids = frozenset(int(value.strip()) for value in raw_admin_ids.split(",") if value.strip())
        except ValueError as error:
            raise RuntimeError("ADMIN_IDS must contain comma-separated numeric Telegram user IDs") from error

        try:
            max_op = int(environ.get("MAX_OP", "20"))
        except ValueError as error:
            raise RuntimeError("MAX_OP must be an integer") from error
        if not 1 <= max_op <= 30:
            raise RuntimeError("MAX_OP must be between 1 and 30")

        return cls(
            bot_token=required["BOT_TOKEN"],
            botohub_token=required["BOTOHUB_TOKEN"],
            database_url=required["DATABASE_URL"],
            redis_url=environ.get("REDIS_URL"),
            admin_ids=admin_ids,
            max_op=max_op,
        )
