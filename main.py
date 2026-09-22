"""Production entry point: configure dependencies and begin long polling."""
from __future__ import annotations
import asyncio, logging
import aiohttp
from aiogram import Bot, Dispatcher
from op_bot.botohub import BotoHubService
from op_bot.config import Settings
from op_bot.handlers.core import router
async def run() -> None:
 settings=Settings.from_env()
 async with aiohttp.ClientSession() as session:
  bot=Bot(settings.bot_token); dp=Dispatcher(botohub=BotoHubService(settings.botohub_token,session))
  dp.include_router(router)
  await dp.start_polling(bot)
if __name__ == '__main__':
 logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(name)s %(message)s')
 asyncio.run(run())
