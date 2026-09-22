"""Production entry point: configure dependencies and begin long polling."""
from __future__ import annotations
import asyncio, logging
import aiohttp
from aiogram import Bot, Dispatcher
from op_bot.botohub import BotoHubService
from op_bot.config import Settings
from op_bot.handlers.core import router
from op_bot.database.session import create_session_factory
from op_bot.database.services import TaskService, UserService
from op_bot.database.block_repository import PostgresBlockedResourceRepository
from op_bot.link_resolver import LinkResolver
from op_bot.resource_blocks import ResourceBlockService
from op_bot.sponsors import SponsorService
async def run() -> None:
 settings=Settings.from_env()
 async with aiohttp.ClientSession() as session:
  engine, sessions = create_session_factory(settings.database_url)
  botohub = BotoHubService(settings.botohub_token, session)
  blocks = ResourceBlockService(PostgresBlockedResourceRepository(sessions))
  sponsor_service = SponsorService(botohub, blocks, LinkResolver(), max_op=settings.max_op)
  bot=Bot(settings.bot_token); dp=Dispatcher(botohub=botohub, sponsor_service=sponsor_service, users=UserService(sessions), task_service=TaskService(sessions))
  dp.include_router(router)
  try:
   await dp.start_polling(bot)
  finally:
   await bot.session.close()
   await engine.dispose()
if __name__ == '__main__':
 logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(name)s %(message)s')
 asyncio.run(run())
