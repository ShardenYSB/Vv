"""Repository protocols make services usable with PostgreSQL implementations."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class BlockedResource:
    resource_id: str
    url: str
    reason: str | None = None


class BlockedResourceRepository(Protocol):
    async def get_active_ids(self) -> list[str]: ...
    async def is_active(self, resource_id: str) -> bool: ...
    async def block(self, *, resource_id: str, url: str, admin_id: int, reason: str | None) -> None: ...
    async def unblock(self, resource_id: str) -> bool: ...
    async def list_active(self) -> list[BlockedResource]: ...


class InMemoryBlockedResourceRepository:
    """Small deterministic repository, useful in tests and local development."""
    def __init__(self) -> None:
        self.items: dict[str, BlockedResource] = {}

    async def get_active_ids(self) -> list[str]: return list(self.items)
    async def is_active(self, resource_id: str) -> bool: return resource_id in self.items
    async def block(self, *, resource_id: str, url: str, admin_id: int, reason: str | None) -> None:
        self.items[resource_id] = BlockedResource(resource_id, url, reason)
    async def unblock(self, resource_id: str) -> bool: return self.items.pop(resource_id, None) is not None
    async def list_active(self) -> list[BlockedResource]: return list(self.items.values())
