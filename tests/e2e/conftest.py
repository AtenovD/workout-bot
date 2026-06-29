"""
Shared fixtures for end-to-end tests.
Simulates a full Telegram bot environment with in-memory SQLite and mocked Bot.
"""
import asyncio
from datetime import date, datetime

import pytest
import pytest_asyncio
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, Update, User as TelegramUser
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.db import Base
from models.user import User
from models.profile import Profile
from models.gamification import UserStats
from models.exercise import (
    Exercise,
    MuscleGroup,
    EquipmentCategory,
    Equipment,
    ExerciseType,
)


# ── Database fixtures ──────────────────────────────────────────────

@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    import models
    eng = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine):
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as s:
        async with s.begin() as txn:
            yield s
            await txn.rollback()


# ── Bot / Dispatcher fixtures ──────────────────────────────────────

class MockTelegramServer(TelegramAPIServer):
    @property
    def base_url(self):
        return "http://testserver/"


class MockSession(AiohttpSession):
    def __init__(self):
        super().__init__(api=MockTelegramServer(base="http://testserver/bot", file="http://testserver/file/bot"))
        self.requests = []

    async def make_request(self, bot, method, **kwargs):
        method_name = getattr(method, "__api_method__", method.__class__.__name__)
        payload = method.model_dump(warnings=False) if hasattr(method, "model_dump") else dict(kwargs)
        self.requests.append({"method": method_name, "payload": payload})
        if method_name == "answerCallbackQuery":
            return True
        if method_name == "getMe":
            return TelegramUser(id=123456, is_bot=True, first_name="TestBot", username="test_workout_bot")
        return {
            "ok": True,
            "result": {
                "message_id": payload.get("message_id", 42),
                "date": int(datetime.utcnow().timestamp()),
                "chat": {"id": payload.get("chat_id", 123456), "type": "private"},
                "from": {"id": 123456, "is_bot": True, "first_name": "TestBot"},
            },
        }


@pytest_asyncio.fixture
async def bot():
    b = Bot(token="123456:ABC-DEF1234gh", session=MockSession())
    yield b
    await b.session.close()


@pytest_asyncio.fixture
async def storage():
    s = MemoryStorage()
    yield s
    await s.close()


@pytest_asyncio.fixture(autouse=True)
async def clear_storage(dispatcher):
    """Automatically clear FSM storage before each test (function scope)."""
    # Clear all state from previous tests
    if hasattr(dispatcher.storage, 'data'):
        # MemoryStorage stores state in .data dict
        dispatcher.storage.data.clear()
    yield


@pytest_asyncio.fixture(scope="session")
async def dispatcher(event_loop, engine):
    """
    Session-scoped Dispatcher: created once per test session.
    Routers are global singletons and cannot be re-attached to multiple dispatchers.
    """
    # Session-scoped storage for the entire session
    session_storage = MemoryStorage()
    dp = Dispatcher(storage=session_storage)

    # Create a middleware that provides fresh session for each event
    class TestDbSessionMiddleware(BaseMiddleware):
        def __init__(self, session_maker):
            self.session_maker = session_maker

        async def __call__(self, handler, event, data):
            async with self.session_maker() as session:
                data["session"] = session
                result = await handler(event, data)
                await session.commit()
                return result

    class TestUserMiddleware(BaseMiddleware):
        async def __call__(self, handler, event, data):
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
                        username=tg_user.username or f"user_{tg_user.id}",
                        first_name=tg_user.first_name or "User",
                        language_code="en",
                    )
                    session.add(user)
                    await session.flush()

                data["user"] = user

            return await handler(event, data)

    # Register middlewares
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    dp.update.middleware(TestDbSessionMiddleware(session_maker))
    dp.update.middleware(TestUserMiddleware())

    # Include routers in the same order as bot/main.py.
    from bot.handlers import onboarding, workout, progress, stats, profile, achievements, schedule, menu
    from bot.handlers.calibration import router as calibration_router
    from bot.handlers.equipment import router as equipment_router
    from bot.handlers.gamification import router as gamification_router
    from bot.handlers.reminder import router as reminder_router
    from bot.handlers.measurements import router as measurements_router
    from bot.handlers.referral import router as referral_router
    from bot.handlers.settings import router as settings_router
    from bot.handlers.challenge import router as challenge_router
    from bot.handlers.help import router as help_router
    from bot.handlers.admin import router as admin_router

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

    # Start polling in background (will run for entire session)
    # Note: we don't create bot here, it's passed per-test
    yield dp

    # Cleanup at session end
    await session_storage.close()


# ── Seed data ──────────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="session")
async def seed_exercises(engine):
    """Create muscle groups + equipment + exercises for workout generation."""
    # Create a session for seeding
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        # Muscle groups (table, not enum)
        mgs = {
            "legs": MuscleGroup(id=1, code="legs", name_ru="Ноги", name_en="Legs", body_part="lower"),
            "chest": MuscleGroup(id=2, code="chest", name_ru="Грудь", name_en="Chest", body_part="upper"),
            "back": MuscleGroup(id=3, code="back", name_ru="Спина", name_en="Back", body_part="upper"),
            "shoulders": MuscleGroup(id=4, code="shoulders", name_ru="Плечи", name_en="Shoulders", body_part="upper"),
            "arms": MuscleGroup(id=5, code="arms", name_ru="Руки", name_en="Arms", body_part="upper"),
            "abs": MuscleGroup(id=6, code="abs", name_ru="Пресс", name_en="Abs", body_part="core"),
        }
        session.add_all(mgs.values())
        await session.flush()
        await session.commit()

        # Equipment items (table, not enum)
        eq = {
            "barbell": Equipment(id=1, code="barbell", name_ru="Штанга", name_en="Barbell",
                                 category=EquipmentCategory.stationary, icon="🏋️"),
            "dumbbells": Equipment(id=2, code="dumbbells", name_ru="Гантели", name_en="Dumbbells",
                                   category=EquipmentCategory.portable, icon="🏋️‍♂️"),
            "bench": Equipment(id=3, code="bench", name_ru="Скамья", name_en="Bench",
                               category=EquipmentCategory.stationary, icon="🪑"),
            "bodyweight": Equipment(id=4, code="bodyweight", name_ru="Свой вес", name_en="Bodyweight",
                                    category=EquipmentCategory.none, icon="🧘"),
            "pullup_bar": Equipment(id=5, code="pullup_bar", name_ru="Турник", name_en="Pull-up Bar",
                                    category=EquipmentCategory.portable, icon="🔝"),
        }
        session.add_all(eq.values())
        await session.flush()
        await session.commit()

        exercises = [
            Exercise(
                id=1,
                code="barbell_squat", name_ru="Приседания со штангой", name_en="Barbell Squat",
                primary_muscle_group_id=mgs["legs"].id,
                required_equipment_id=eq["barbell"].id,
                equipment_category=EquipmentCategory.stationary,
                exercise_type=ExerciseType.compound,
                gif_url="https://ex.com/sq.gif",
            ),
            Exercise(
                id=2,
                code="bench_press", name_ru="Жим лёжа", name_en="Bench Press",
                primary_muscle_group_id=mgs["chest"].id,
                required_equipment_id=eq["barbell"].id,
                equipment_category=EquipmentCategory.stationary,
                exercise_type=ExerciseType.compound,
                gif_url="https://ex.com/bp.gif",
            ),
            Exercise(
                id=3,
                code="deadlift", name_ru="Становая тяга", name_en="Deadlift",
                primary_muscle_group_id=mgs["back"].id,
                required_equipment_id=eq["barbell"].id,
                equipment_category=EquipmentCategory.stationary,
                exercise_type=ExerciseType.compound,
                gif_url="https://ex.com/dl.gif",
            ),
            Exercise(
                id=4,
                code="pushups", name_ru="Отжимания", name_en="Push-ups",
                primary_muscle_group_id=mgs["chest"].id,
                required_equipment_id=eq["bodyweight"].id,
                equipment_category=EquipmentCategory.none,
                exercise_type=ExerciseType.compound,
                gif_url="https://ex.com/pu.gif",
            ),
            Exercise(
                id=5,
                code="pullups", name_ru="Подтягивания", name_en="Pull-ups",
                primary_muscle_group_id=mgs["back"].id,
                required_equipment_id=eq["pullup_bar"].id,
                equipment_category=EquipmentCategory.portable,
                exercise_type=ExerciseType.compound,
                gif_url="https://ex.com/pull.gif",
            ),
            Exercise(
                id=6,
                code="db_shoulder_press", name_ru="Жим гантелей сидя", name_en="DB Shoulder Press",
                primary_muscle_group_id=mgs["shoulders"].id,
                required_equipment_id=eq["dumbbells"].id,
                equipment_category=EquipmentCategory.portable,
                exercise_type=ExerciseType.compound,
                gif_url="https://ex.com/dbp.gif",
            ),
        ]
        session.add_all(exercises)
        await session.flush()
        await session.commit()
        return exercises


@pytest_asyncio.fixture
async def registered_user(engine, seed_exercises):
    """A fully onboarded user with complete profile."""
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        # Clear any existing user with this telegram_id and their profile
        existing = await session.execute(select(User).where(User.telegram_id == 123456789))
        existing_user = existing.scalar_one_or_none()
        if existing_user:
            await session.execute(delete(UserStats).where(UserStats.user_id == existing_user.id))
            await session.execute(delete(Profile).where(Profile.user_id == existing_user.id))
        await session.execute(delete(User).where(User.telegram_id == 123456789))
        await session.commit()

        user = User(
            telegram_id=123456789,
            username="testuser",
            first_name="Тест",
            language_code="ru",
        )
        session.add(user)
        await session.flush()

        profile = Profile(
            user_id=user.id,
            gender="male",
            birth_date=date(1995, 1, 1),
            height_cm=180,
            current_weight_kg=80.0,
            goal="mass_gain",
            experience_level="intermediate",
            training_structure="fullbody",
            preferred_duration_min=45,
            health_flags=[],
            calibrated_at=datetime.utcnow(),
        )
        session.add(profile)
        session.add(UserStats(id=1, user_id=user.id, level=1, total_xp=0))
        await session.flush()
        await session.commit()

        return user
