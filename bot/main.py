"""
Bot entry point — creates bot, dispatcher, registers all handlers and middlewares.
"""
import asyncio
import logging
import os

import structlog
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from core.config import settings
from core.db import AsyncSessionLocal
from bot.middlewares.db import DbSessionMiddleware
from bot.middlewares.user import UserMiddleware
from bot.services.scheduler import start_scheduler

# Legacy module-style routers (existing handlers)
from bot.handlers import (
    onboarding,
    workout,
    progress,
    stats,
    profile,
    achievements,
    schedule,
    menu,
)

# New individual routers
from bot.handlers.calibration import router as calibration_router
from bot.handlers.equipment import router as equipment_router
from bot.handlers.gamification import router as gamification_router
from bot.handlers.reminder import router as reminder_router
from bot.handlers.measurements import router as measurements_router
from bot.handlers.referral import router as referral_router
from bot.handlers.settings import router as settings_router
from bot.handlers.challenge import router as challenge_router
from bot.handlers.help import router as help_router
from bot.handlers.admin import router as admin_router, set_admins

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO)
)
log = structlog.get_logger()


async def main() -> None:
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    redis = Redis.from_url(settings.REDIS_URL)
    storage = RedisStorage(redis=redis)
    dp = Dispatcher(storage=storage)

    # Middlewares (order matters: db first, then user)
    dp.update.middleware(DbSessionMiddleware(AsyncSessionLocal))
    dp.update.middleware(UserMiddleware())

    # Load admin IDs from env
    admin_ids = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip().isdigit()]
    set_admins(admin_ids)

    # Register all routers
    # Note: onboarding handles /start and initial calibration flow
    # calibration_router handles /calibration command (re-calibration)
    dp.include_routers(
        onboarding.router,
        menu.router,
        calibration_router,
        equipment_router,
        workout.router,
        gamification_router,
        measurements_router,
        reminder_router,
        referral_router,
        settings_router,
        challenge_router,
        help_router,
        admin_router,
        progress.router,
        stats.router,
        profile.router,
        achievements.router,
        schedule.router,
    )

    log.info("Starting bot", bot_username=(await bot.get_me()).username)

    await bot.delete_webhook(drop_pending_updates=True)
    start_scheduler(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
