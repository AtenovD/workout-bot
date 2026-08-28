from typing import Callable, Awaitable, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from core.redis import redis_client


class ThrottleMiddleware(BaseMiddleware):
    RATE_LIMIT = 1  # seconds between messages

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
            if user_id:
                key = f"throttle:{user_id}"
                if await redis_client.exists(key):
                    return  # Rate limited
                await redis_client.setex(key, self.RATE_LIMIT, "1")

        return await handler(event, data)
