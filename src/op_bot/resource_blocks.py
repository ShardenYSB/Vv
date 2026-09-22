"""Blacklist business rules, kept independent of the Telegram framework."""
from __future__ import annotations
from .repositories import BlockedResourceRepository, BlockedResource


class ResourceBlockService:
    def __init__(self, repository: BlockedResourceRepository) -> None:
        self._repository = repository

    async def is_blocked(self, resource_id: str | int | None) -> bool:
        return bool(resource_id) and await self._repository.is_active(str(resource_id))

    async def block(self, resource_id: str | int, url: str, admin_id: int, reason: str | None = None) -> None:
        if not str(resource_id):
            raise ValueError("resource_id must not be empty")
        await self._repository.block(resource_id=str(resource_id), url=url, admin_id=admin_id, reason=reason)

    async def unblock(self, resource_id: str | int) -> bool:
        return await self._repository.unblock(str(resource_id))

    async def get_blocked_ids(self) -> list[str]:
        return await self._repository.get_active_ids()

    async def list_blocked(self) -> list[BlockedResource]:
        return await self._repository.list_active()
