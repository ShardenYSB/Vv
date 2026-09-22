"""Persistence-facing workflow for resources whose Telegram URL cannot be resolved."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True, slots=True)
class UnresolvedResource:
    id: int
    url: str
    resource_id: str | None
    user_id: int
    status: str
    error_type: str

class UnresolvedRepository(Protocol):
    async def create(self, *, url: str, resource_id: str | None, user_id: int, error_type: str) -> UnresolvedResource: ...
    async def set_status(self, unresolved_id: int, status: str, admin_id: int) -> None: ...

class UnresolvedResourceService:
    def __init__(self, repository: UnresolvedRepository) -> None:
        self._repository = repository

    async def report(self, url: str, resource_id: str | None, user_id: int, error_type: str) -> UnresolvedResource:
        return await self._repository.create(url=url, resource_id=resource_id, user_id=user_id, error_type=error_type)

    async def mark_blocked(self, unresolved_id: int, admin_id: int) -> None:
        await self._repository.set_status(unresolved_id, "blocked", admin_id)

    async def ignore(self, unresolved_id: int, admin_id: int) -> None:
        await self._repository.set_status(unresolved_id, "ignored", admin_id)
