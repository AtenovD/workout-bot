from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models.user import User
from models.profile import Profile
from models.gamification import UserStats


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_profile(self, user_id: int) -> Profile | None:
        result = await self.session.execute(
            select(Profile).where(Profile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_stats(self, user_id: int) -> UserStats | None:
        result = await self.session.execute(
            select(UserStats).where(UserStats.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_user(self, telegram_id: int, username: str | None, first_name: str | None, language_code: str = "ru") -> User:
        user = User(telegram_id=telegram_id, username=username, first_name=first_name, language_code=language_code)
        self.session.add(user)
        await self.session.flush()
        stats = UserStats(user_id=user.id)
        self.session.add(stats)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_profile(self, user_id: int, **kwargs) -> Profile:
        result = await self.session.execute(select(Profile).where(Profile.user_id == user_id))
        profile = result.scalar_one_or_none()
        if not profile:
            profile = Profile(user_id=user_id, **kwargs)
            self.session.add(profile)
        else:
            for key, value in kwargs.items():
                setattr(profile, key, value)
        await self.session.commit()
        await self.session.refresh(profile)
        return profile
