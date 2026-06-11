"""
Bot entry point. Registers all routers and middlewares.
"""
import asyncio
import logging
import structlog
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand

from core.config import settings
from core.redis import redis_client
from bot.handlers import onboarding, workout, equipment, progress, gamification, profile, common, schedule
from bot.middlewares.user_middleware import UserMiddleware
from bot.middlewares.throttle_middleware import ThrottleMiddleware

logger = structlog.get_logger()


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запуск / калибровка"),
        BotCommand(command="workout", description="Начать тренировку"),
        BotCommand(command="progress", description="Мой прогресс"),
        BotCommand(command="menu", description="Главное меню"),
        BotCommand(command="settings", description="Настройки"),
        BotCommand(command="help", description="Помощь"),
    ]
    await bot.set_my_commands(commands)


async def main():
    logging.basicConfig(level=settings.log_level)

    if settings.sentry_dsn:
        import sentry_sdk
        sentry_sdk.init(dsn=settings.sentry_dsn)

    bot = Bot(token=settings.bot_token)
    storage = RedisStorage(redis=redis_client)
    dp = Dispatcher(storage=storage)

    # Middlewares
    dp.update.middleware(UserMiddleware())
    dp.message.middleware(ThrottleMiddleware())

    # Routers
    dp.include_router(onboarding.router)
    dp.include_router(workout.router)
    dp.include_router(equipment.router)
    dp.include_router(progress.router)
    dp.include_router(gamification.router)
    dp.include_router(profile.router)
    dp.include_router(schedule.router)
    dp.include_router(common.router)

    await set_commands(bot)
    logger.info("Bot started", env=settings.app_env)

    if settings.webhook_host:
        from aiohttp import web
        app = web.Application()
        # webhook setup
        await bot.set_webhook(f"{settings.webhook_host}{settings.webhook_path}")
        logger.info("Running in webhook mode", url=f"{settings.webhook_host}{settings.webhook_path}")
    else:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
