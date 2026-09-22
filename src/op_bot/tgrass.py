"""Client for Tgrass mandatory offers and task offers API."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import aiohttp


class TgrassError(RuntimeError):
    pass


class TgrassTemporaryError(TgrassError):
    pass


@dataclass(frozen=True, slots=True)
class TgrassUser:
    telegram_id: int
    username: str | None
    language_code: str | None
    is_premium: bool

    def payload(self) -> dict[str, Any]:
        return {
            "tg_user_id": self.telegram_id,
            "tg_login": self.username,
            "lang": self.language_code or "ru",
            "is_premium": self.is_premium,
        }


class TgrassService:
    BASE_URL = "https://tgrass.space"

    def __init__(self, token: str, session: aiohttp.ClientSession, timeout: float = 12) -> None:
        self._token = token
        self._session = session
        self._timeout = timeout

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            async with self._session.post(
                f"{self.BASE_URL}{path}", json=payload,
                headers={"Accept": "application/json", "Content-Type": "application/json", "Auth": self._token},
                timeout=self._timeout,
            ) as response:
                if response.status == 401:
                    raise TgrassError("Tgrass rejected credentials")
                if response.status == 429 or response.status >= 500:
                    raise TgrassTemporaryError("Tgrass temporarily unavailable")
                if response.status >= 400:
                    raise TgrassError(f"Tgrass request failed with HTTP {response.status}")
                data = await response.json()
                if not isinstance(data, dict):
                    raise TgrassError("Unexpected Tgrass response")
                return data
        except (aiohttp.ClientError, asyncio.TimeoutError) as error:
            raise TgrassTemporaryError("Tgrass request failed") from error

    async def get_offers(self, user: TgrassUser, *, tasks: bool = False, exclude_channels: list[str] | None = None, limit: int | None = None) -> dict[str, Any]:
        payload = user.payload()
        if exclude_channels:
            payload["exclude_channels"] = exclude_channels
        if limit:
            payload["offers_limit"] = limit
        return await self._post("/tasks" if tasks else "/offers", payload)

    async def check_offer(self, telegram_id: int, offer_id: int) -> dict[str, Any]:
        return await self._post("/check", {"tg_user_id": telegram_id, "offer_id": offer_id})

    async def reset_offers(self, telegram_id: int) -> dict[str, Any]:
        return await self._post("/reset_offers", {"tg_user_id": telegram_id})
