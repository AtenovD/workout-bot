from typing import Callable, Awaitable, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from core.db import AsyncSessionLocal
from models.user import User, UserStatus
from models.gamification import UserStats
from sqlalchemy import select


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = None
        if isinstance(event, (Message, CallbackQuery)):
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
                    )
                    session.add(user)
                    stats = UserStats(user_id=user.id)
                    session.add(stats)
                    await session.commit()
                    await session.refresh(user)

                if user.status == UserStatus.banned:
                    return  # Ignore banned users

                data["user"] = user
                data["session"] = session

        return await handler(event, data)
