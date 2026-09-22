"""Typed aiohttp client for BotoHub; handlers never call HTTP directly."""
from __future__ import annotations
from typing import Any
import asyncio
import aiohttp

class BotoHubError(RuntimeError): pass
class BotoHubTemporaryError(BotoHubError): pass
class BotoHubAuthError(BotoHubError): pass

class BotoHubService:
    BASE_URL = "https://botohub.me"
    def __init__(self, token: str, session: aiohttp.ClientSession, timeout: float = 12) -> None:
        self._token, self._session, self._timeout = token, session, timeout

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            async with self._session.post(f"{self.BASE_URL}{path}", json=payload,
                headers={"Auth": self._token, "Content-Type": "application/json"}, timeout=self._timeout) as response:
                if response.status == 401: raise BotoHubAuthError("BotoHub rejected credentials")
                if response.status == 400: raise BotoHubError("BotoHub rejected request")
                if response.status == 429 or response.status >= 500: raise BotoHubTemporaryError("BotoHub temporarily unavailable")
                response.raise_for_status()
                data = await response.json()
                if not isinstance(data, dict): raise BotoHubError("Unexpected BotoHub response")
                return data
        except (aiohttp.ClientError, asyncio.TimeoutError) as error:
            raise BotoHubTemporaryError("BotoHub request failed") from error

    async def get_sponsors(self, chat_id: int, max_op: int = 20, excluded_ids: list[str] | None = None) -> dict[str, Any]:
        return await self._post("/get-tasks-extended", {"chat_id": chat_id, "max_op": max_op, "only_has_check": True, "excluded_ids": excluded_ids or []})

    async def get_tasks_extended(self, **kwargs: Any) -> dict[str, Any]:
        """Protocol-compatible name used by SponsorService."""
        return await self._post("/get-tasks-extended", kwargs)
    async def check_sponsors(self, chat_id: int, max_op: int = 20, excluded_ids: list[str] | None = None) -> dict[str, Any]:
        return await self.get_sponsors(chat_id, max_op, excluded_ids)
    async def get_task(self, chat_id: int, skip: bool = False) -> dict[str, Any]:
        return await self._post("/get-tasks", {"chat_id": chat_id, "is_task": True, "skip": skip})
