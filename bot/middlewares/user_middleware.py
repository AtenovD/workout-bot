from typing import Callable, Awaitable, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from core.db import AsyncSessionLocal
from models.user import User, UserStatus
from models.gamification import UserStats
from sqlalchemy import select
from datetime import datetime


class UserMiddleware(BaseMiddleware):
    """Injects current User + AsyncSession into handler data."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = None
        if isinstance(event, Message):
            tg_user = event.from_user
        elif isinstance(event, CallbackQuery):
            tg_user = event.from_user

        if tg_user:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(User).where(User.telegram_id == tg_user.id)
                )
                user = result.scalar_one_or_none()

                if not user:
                    user = User(
                        telegram_id=tg_user.id,
                        username=tg_user.username,
                        first_name=tg_user.first_name,
                        language_code=tg_user.language_code or "ru",
                        status=UserStatus.active,
                        last_active_at=datetime.utcnow(),
                    )
                    session.add(user)
                    await session.flush()

                    # Create UserStats immediately on first encounter
                    stats = UserStats(user_id=user.id)
                    session.add(stats)
                    await session.commit()
                    await session.refresh(user)
                else:
                    # Ensure UserStats exists for old users
                    stats_res = await session.execute(
                        select(UserStats).where(UserStats.user_id == user.id)
                    )
                    if not stats_res.scalar_one_or_none():
                        session.add(UserStats(user_id=user.id))

                    user.last_active_at = datetime.utcnow()
                    await session.commit()
                    await session.refresh(user)

                data["user"] = user
                data["session"] = session

        return await handler(event, data)
