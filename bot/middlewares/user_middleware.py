from typing import Callable, Awaitable, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from core.db import AsyncSessionLocal
from models.user import User, UserStatus
from models.gamification import UserStats
from sqlalchemy import select, func
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
                    )
                    session.add(user)
                    await session.flush()
                    stats = UserStats(user_id=user.id)
                    session.add(stats)
                    await session.commit()
                    await session.refresh(user)
                else:
                    # Update last_active_at
                    user.last_active_at = datetime.utcnow()
                    await session.commit()

                if user.status == UserStatus.banned:
                    if isinstance(event, Message):
                        await event.answer("⛔ Ваш аккаунт заблокирован.")
                    elif isinstance(event, CallbackQuery):
                        await event.answer("⛔ Аккаунт заблокирован.", show_alert=True)
                    return

                data["user"] = user
                data["session"] = session
                return await handler(event, data)

        return await handler(event, data)
