"""PostgreSQL implementation of the resource blacklist repository."""
from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from op_bot.database.models import BlockedResourceModel
from op_bot.repositories import BlockedResource


class PostgresBlockedResourceRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def get_active_ids(self) -> list[str]:
        async with self._sessions() as session:
            result = await session.scalars(select(BlockedResourceModel.resource_id).where(BlockedResourceModel.is_active.is_(True)))
            return list(result.all())

    async def is_active(self, resource_id: str) -> bool:
        async with self._sessions() as session:
            return await session.scalar(select(BlockedResourceModel.id).where(BlockedResourceModel.resource_id == resource_id, BlockedResourceModel.is_active.is_(True))) is not None

    async def block(self, *, resource_id: str, url: str, admin_id: int, reason: str | None) -> None:
        """Create or reactivate a block without violating the active partial index."""
        async with self._sessions() as session, session.begin():
            existing = await session.scalar(select(BlockedResourceModel).where(BlockedResourceModel.resource_id == resource_id).order_by(BlockedResourceModel.id.desc()).with_for_update())
            if existing:
                existing.url = url
                existing.reason = reason
                existing.blocked_by = admin_id
                existing.is_active = True
            else:
                session.add(BlockedResourceModel(resource_id=resource_id, url=url, blocked_by=admin_id, reason=reason))

    async def unblock(self, resource_id: str) -> bool:
        async with self._sessions() as session, session.begin():
            result = await session.execute(update(BlockedResourceModel).where(BlockedResourceModel.resource_id == resource_id, BlockedResourceModel.is_active.is_(True)).values(is_active=False))
            return result.rowcount > 0

    async def list_active(self) -> list[BlockedResource]:
        async with self._sessions() as session:
            result = await session.scalars(select(BlockedResourceModel).where(BlockedResourceModel.is_active.is_(True)).order_by(BlockedResourceModel.created_at.desc()))
            return [BlockedResource(item.resource_id, item.url, item.reason) for item in result]
