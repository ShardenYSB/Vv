"""Production entry point: configure dependencies and begin long polling."""
from __future__ import annotations

import asyncio
import logging

import aiohttp
from aiogram import Bot, Dispatcher

from op_bot.botohub import BotoHubService
from op_bot.config import Settings
from op_bot.database.admin_service import AdminService
from op_bot.database.block_repository import PostgresBlockedResourceRepository
from op_bot.database.services import TaskService, UserService
from op_bot.database.session import create_session_factory
from op_bot.handlers.admin import router as admin_router
from op_bot.handlers.core import router as core_router
from op_bot.link_resolver import LinkResolver
from op_bot.resource_blocks import ResourceBlockService
from op_bot.sponsors import SponsorService
from op_bot.tgrass import TgrassService


async def run() -> None:
    settings = Settings.from_env()
    engine, sessions = create_session_factory(settings.database_url)
    bot = Bot(settings.bot_token)
    try:
        async with aiohttp.ClientSession() as http_session:
            botohub = BotoHubService(settings.botohub_token, http_session)
            blocks = ResourceBlockService(PostgresBlockedResourceRepository(sessions))
            dispatcher = Dispatcher(
                botohub=botohub,
                sponsor_service=SponsorService(botohub, blocks, LinkResolver(), max_op=settings.max_op),
                users=UserService(sessions),
                task_service=TaskService(sessions),
                blocks=blocks,
                admin_service=AdminService(sessions),
                settings=settings,
                tgrass=TgrassService(settings.tgrass_token, http_session) if settings.tgrass_token else None,
            )
            dispatcher.include_router(core_router)
            dispatcher.include_router(admin_router)
            await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    asyncio.run(run())
