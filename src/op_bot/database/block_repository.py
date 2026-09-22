from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from op_bot.repositories import BlockedResource
from op_bot.database.models import BlockedResourceModel
class PostgresBlockedResourceRepository:
 def __init__(self,sessions:async_sessionmaker[AsyncSession]): self.sessions=sessions
 async def get_active_ids(self):
  async with self.sessions() as s: return list((await s.scalars(select(BlockedResourceModel.resource_id).where(BlockedResourceModel.is_active.is_(True)))).all())
 async def is_active(self,resource_id):
  async with self.sessions() as s: return await s.scalar(select(BlockedResourceModel.id).where(BlockedResourceModel.resource_id==resource_id,BlockedResourceModel.is_active.is_(True))) is not None
 async def block(self,*,resource_id,url,admin_id,reason):
  async with self.sessions() as s, s.begin(): s.add(BlockedResourceModel(resource_id=resource_id,url=url,blocked_by=admin_id,reason=reason))
 async def unblock(self,resource_id):
  async with self.sessions() as s, s.begin(): return (await s.execute(update(BlockedResourceModel).where(BlockedResourceModel.resource_id==resource_id,BlockedResourceModel.is_active.is_(True)).values(is_active=False))).rowcount>0
 async def list_active(self):
  async with self.sessions() as s: return [BlockedResource(x.resource_id,x.url,x.reason) for x in (await s.scalars(select(BlockedResourceModel).where(BlockedResourceModel.is_active.is_(True)))).all()]
