"""Transactional persistence for users, referrals, and internal Stars credits."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from op_bot.rewards import get_referral_reward
from .models import Referral, StarTransaction, Task, User


class UserService:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def register(self, telegram_id: int, username: str | None, first_name: str | None, referrer_telegram_id: int | None = None) -> User:
        async with self._sessions() as session, session.begin():
            user = await session.scalar(select(User).where(User.telegram_id == telegram_id).with_for_update())
            if user:
                return user
            referrer_id = None
            if referrer_telegram_id and referrer_telegram_id != telegram_id:
                referrer = await session.scalar(select(User).where(User.telegram_id == referrer_telegram_id))
                referrer_id = referrer.id if referrer else None
            user = User(telegram_id=telegram_id, username=username, first_name=first_name, referrer_id=referrer_id)
            session.add(user)
            await session.flush()
            if referrer_id:
                session.add(Referral(referrer_id=referrer_id, referred_id=user.id))
            return user

    async def profile(self, telegram_id: int) -> tuple[User, int, int, int]:
        async with self._sessions() as session:
            user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
            if not user:
                raise LookupError("user is not registered")
            referrals = await session.scalar(select(func.count()).select_from(Referral).where(Referral.referrer_id == user.id, Referral.status == "confirmed")) or 0
            tasks = await session.scalar(select(func.count()).select_from(Task).where(Task.user_id == user.id, Task.rewarded.is_(True))) or 0
            earned = await session.scalar(select(func.coalesce(func.sum(StarTransaction.amount), 0)).where(StarTransaction.user_id == user.id, StarTransaction.type == "referral")) or 0
            return user, referrals, tasks, earned

    async def confirm_referral_after_sponsors(self, telegram_id: int, sponsors_count: int) -> int:
        """Confirm once after OP completion and credit the inviter atomically."""
        async with self._sessions() as session, session.begin():
            referred = await session.scalar(select(User).where(User.telegram_id == telegram_id).with_for_update())
            if not referred:
                return 0
            referred.sponsors_completed = True
            referral = await session.scalar(select(Referral).where(Referral.referred_id == referred.id).with_for_update())
            if not referral or referral.status != "pending":
                return 0
            referrer = await session.scalar(select(User).where(User.id == referral.referrer_id).with_for_update())
            if not referrer:
                referral.status = "rejected"
                return 0
            reward = get_referral_reward(sponsors_count)
            referral.status, referral.reward, referral.confirmed_at = "confirmed", reward, datetime.now(timezone.utc)
            if reward:
                referrer.stars_balance += reward
                session.add(StarTransaction(user_id=referrer.id, amount=reward, type="referral", source_id=str(referred.telegram_id), description="Подтверждённый реферал"))
            return reward

    async def has_sponsor_access(self, telegram_id: int) -> bool:
        async with self._sessions() as session:
            return bool(await session.scalar(select(User.sponsors_completed).where(User.telegram_id == telegram_id)))


class TaskService:
    """Tracks the currently displayed BotoHub task and makes payment idempotent."""
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def present(self, telegram_id: int, resource_id: str, url: str, reward: int) -> None:
        async with self._sessions() as session, session.begin():
            user = await session.scalar(select(User).where(User.telegram_id == telegram_id).with_for_update())
            if not user:
                raise LookupError("user is not registered")
            await session.execute(update(Task).where(Task.user_id == user.id, Task.status == "presented", Task.rewarded.is_(False)).values(status="superseded"))
            task = await session.scalar(select(Task).where(Task.user_id == user.id, Task.resource_id == resource_id).with_for_update())
            if task and task.rewarded:
                return
            if task:
                task.url, task.reward, task.status = url, reward, "presented"
            else:
                session.add(Task(user_id=user.id, resource_id=resource_id, url=url, reward=reward, status="presented"))

    async def complete_presented(self, telegram_id: int) -> bool:
        async with self._sessions() as session, session.begin():
            user = await session.scalar(select(User).where(User.telegram_id == telegram_id).with_for_update())
            if not user:
                return False
            task = await session.scalar(select(Task).where(Task.user_id == user.id, Task.status == "presented", Task.rewarded.is_(False)).order_by(Task.id.desc()).with_for_update())
            if not task:
                return False
            task.status, task.rewarded, task.completed_at = "completed", True, datetime.now(timezone.utc)
            user.stars_balance += task.reward
            session.add(StarTransaction(user_id=user.id, amount=task.reward, type="task", source_id=task.resource_id, description="Выполнено задание"))
            return True

    async def abandon_presented(self, telegram_id: int) -> None:
        async with self._sessions() as session, session.begin():
            user = await session.scalar(select(User).where(User.telegram_id == telegram_id).with_for_update())
            if user:
                await session.execute(update(Task).where(Task.user_id == user.id, Task.status == "presented", Task.rewarded.is_(False)).values(status="skipped"))
