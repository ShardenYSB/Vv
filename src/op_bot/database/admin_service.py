"""Read-only dashboard statistics and auditable administrator actions."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .models import AdminLog, BlockedResourceModel, Referral, StarTransaction, Task, User


class AdminService:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def dashboard(self) -> dict[str, int]:
        async with self._sessions() as session:
            async def count(model, *criteria) -> int:
                return int(await session.scalar(select(func.count()).select_from(model).where(*criteria)) or 0)

            stars = await session.scalar(select(func.coalesce(func.sum(StarTransaction.amount), 0)).where(StarTransaction.amount > 0))
            return {
                "users": await count(User),
                "referrals": await count(Referral, Referral.status == "confirmed"),
                "stars": int(stars or 0),
                "tasks": await count(Task, Task.rewarded.is_(True)),
                "blocked": await count(BlockedResourceModel, BlockedResourceModel.is_active.is_(True)),
            }

    async def log(self, admin_id: int, action: str, target_type: str, target_id: str, *, old_value: str | None = None, new_value: str | None = None) -> None:
        async with self._sessions() as session, session.begin():
            session.add(AdminLog(
                admin_id=admin_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                old_value=old_value,
                new_value=new_value,
            ))
