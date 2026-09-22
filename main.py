"""Production entry point: configure dependencies and begin long polling."""
from __future__ import annotations
import asyncio, logging
import aiohttp
from aiogram import Bot, Dispatcher
from op_bot.botohub import BotoHubService
from op_bot.config import Settings
from op_bot.handlers.core import router
from op_bot.database.session import create_session_factory
from op_bot.database.services import UserService
async def run() -> None:
 settings=Settings.from_env()
 async with aiohttp.ClientSession() as session:
  engine, sessions = create_session_factory(settings.database_url)
  bot=Bot(settings.bot_token); dp=Dispatcher(botohub=BotoHubService(settings.botohub_token,session), users=UserService(sessions))
  dp.include_router(router)
  try:
   await dp.start_polling(bot)
  finally:
   await engine.dispose()
if __name__ == '__main__':
 logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(name)s %(message)s')
 asyncio.run(run())
