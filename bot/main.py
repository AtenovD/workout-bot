"""
Bot entry point — creates bot, dispatcher, registers all handlers and middlewares.
"""
import asyncio
import logging

import structlog
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from core.config import settings
from core.db import AsyncSessionLocal
from bot.middlewares.db import DbSessionMiddleware
from bot.middlewares.user import UserMiddleware

# Import all routers
from bot.handlers import (
    start,
    onboarding,
    workout,
    progress,
    stats,
    profile,
    achievements,
    schedule,
    menu,
)

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)
log = structlog.get_logger()


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=settings.BOT_TOKEN, parse_mode=ParseMode.HTML)
    redis = Redis.from_url(settings.REDIS_URL)
    storage = RedisStorage(redis=redis)
    dp = Dispatcher(storage=storage)

    # Middlewares (order matters: db first, then user)
    dp.update.middleware(DbSessionMiddleware(AsyncSessionLocal))
    dp.update.middleware(UserMiddleware())

    # Register routers
    dp.include_routers(
        start.router,
        onboarding.router,
        menu.router,
        workout.router,
        progress.router,
        stats.router,
        profile.router,
        achievements.router,
        schedule.router,
    )

    log.info("Starting bot", bot_username=(await bot.get_me()).username)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
