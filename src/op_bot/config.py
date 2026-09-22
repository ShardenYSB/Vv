"""Runtime configuration. Secrets are read exclusively from the environment."""
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
        required = {key: environ.get(key) for key in ("BOT_TOKEN", "BOTOHUB_TOKEN", "DATABASE_URL")}
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
        ids = frozenset(int(value) for value in environ.get("ADMIN_IDS", "").split(",") if value.strip())
        return cls(required["BOT_TOKEN"] or "", required["BOTOHUB_TOKEN"] or "", required["DATABASE_URL"] or "", environ.get("REDIS_URL"), ids, int(environ.get("MAX_OP", "20")))
