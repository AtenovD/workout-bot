from core.db import AsyncSessionLocal


async def get_session():
    return AsyncSessionLocal()
