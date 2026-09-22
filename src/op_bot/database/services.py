"""Transactional application persistence. All Stars writes go through this module."""
from __future__ import annotations
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from .models import Referral, StarTransaction, Task, User

class UserService:
 def __init__(self, sessions: async_sessionmaker[AsyncSession]): self._sessions=sessions
 async def register(self, telegram_id: int, username: str|None, first_name: str|None, referrer_telegram_id: int|None=None) -> User:
  async with self._sessions() as s, s.begin():
   user=await s.scalar(select(User).where(User.telegram_id==telegram_id).with_for_update())
   if user: return user
   referrer_id=None
   if referrer_telegram_id and referrer_telegram_id != telegram_id:
    referrer=await s.scalar(select(User).where(User.telegram_id==referrer_telegram_id))
    referrer_id=referrer.id if referrer else None
   user=User(telegram_id=telegram_id,username=username,first_name=first_name,referrer_id=referrer_id)
   s.add(user); await s.flush()
   if referrer_id: s.add(Referral(referrer_id=referrer_id,referred_id=user.id))
   return user
 async def profile(self, telegram_id: int) -> tuple[User,int,int,int]:
  async with self._sessions() as s:
   user=await s.scalar(select(User).where(User.telegram_id==telegram_id))
   if not user: raise LookupError('user is not registered')
   referrals=await s.scalar(select(func.count()).select_from(Referral).where(Referral.referrer_id==user.id,Referral.status=='confirmed')) or 0
   tasks=await s.scalar(select(func.count()).select_from(Task).where(Task.user_id==user.id,Task.rewarded.is_(True))) or 0
   earned=await s.scalar(select(func.coalesce(func.sum(StarTransaction.amount),0)).where(StarTransaction.user_id==user.id,StarTransaction.type=='referral')) or 0
   return user,referrals,tasks,earned

class StarsService:
 def __init__(self,sessions: async_sessionmaker[AsyncSession]): self._sessions=sessions
 async def reward_task_once(self, telegram_id:int, resource_id:str, url:str, reward:int) -> bool:
  """Idempotent task payment: task row is locked and ledger+balance commit together."""
  async with self._sessions() as s, s.begin():
   user=await s.scalar(select(User).where(User.telegram_id==telegram_id).with_for_update())
   task=await s.scalar(select(Task).where(Task.user_id==user.id,Task.resource_id==resource_id).with_for_update())
   if task and task.rewarded: return False
   if not task: task=Task(user_id=user.id,resource_id=resource_id,url=url,reward=reward,status='completed',rewarded=True); s.add(task)
   else: task.status='completed'; task.reward=reward; task.rewarded=True
   user.stars_balance+=reward; s.add(StarTransaction(user_id=user.id,amount=reward,type='task',source_id=resource_id,description='Выполнено задание'))
   return True
