from typing import Callable, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from models.user import User
from models.gamification import UserStats


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        session: AsyncSession = data.get("session")
        if not session:
            return await handler(event, data)

        tg_user = None
        if isinstance(event, Update):
            if event.message:
                tg_user = event.message.from_user
            elif event.callback_query:
                tg_user = event.callback_query.from_user

        if tg_user:
            res = await session.execute(select(User).where(User.telegram_id == tg_user.id))
            user = res.scalar_one_or_none()

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
                user.last_active_at = datetime.utcnow()
                await session.commit()

            data["user"] = user

        return await handler(event, data)
