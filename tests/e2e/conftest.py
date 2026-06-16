"""
Shared fixtures for end-to-end tests.
Simulates a full Telegram bot environment with in-memory SQLite and mocked Bot.
"""
import asyncio
from datetime import date, datetime

import pytest
import pytest_asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.db import Base
from models.user import User
from models.profile import Profile
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
        super().__init__(api=MockTelegramServer())

    async def make_request(self, bot, method, **kwargs):
        return {
            "ok": True,
            "result": {
                "message_id": kwargs.get("message_id", 42),
                "date": int(datetime.utcnow().timestamp()),
                "chat": {"id": kwargs.get("chat_id", 123456), "type": "private"},
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


@pytest_asyncio.fixture
async def dispatcher(bot, storage, session, engine):
    """
    Fully wired Dispatcher with middlewares that replicate the real app:
      - Injects `session` (the test's AsyncSession)
      - Injects `user`  (User model looked up by telegram_id)
    """
    dp = Dispatcher(storage=storage)

    # Replicate UserMiddleware — inject user from DB
    async def user_mw(handler, event, data):
        tg_user = None
        if isinstance(event, Message):
            tg_user = event.from_user
        elif isinstance(event, CallbackQuery):
            tg_user = event.from_user

        if tg_user:
            s = data.get("session")
            if s is None:
                # Create a fresh session if none provided
                maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
                async with maker() as fresh_s:
                    res = await fresh_s.execute(select(User).where(User.telegram_id == tg_user.id))
                    u = res.scalar_one_or_none()
                    data["user"] = u
                    data["session"] = fresh_s
                    return await handler(event, data)
            else:
                res = await s.execute(select(User).where(User.telegram_id == tg_user.id))
                u = res.scalar_one_or_none()
                data["user"] = u

        return await handler(event, data)

    dp.update.outer_middleware(user_mw)

    # Include all routers
    from bot.handlers.onboarding import router as onboarding_router
    from bot.handlers.menu import router as menu_router
    from bot.handlers.calibration import router as calibration_router
    from bot.handlers.workout import router as workout_router
    from bot.handlers.progress import router as progress_router
    from bot.handlers.schedule import router as schedule_router
    from bot.handlers.challenge import router as challenge_router
    from bot.handlers.equipment import router as equipment_router
    from bot.handlers.achievements import router as achievements_router

    dp.include_router(onboarding_router)
    dp.include_router(menu_router)
    dp.include_router(calibration_router)
    dp.include_router(workout_router)
    dp.include_router(progress_router)
    dp.include_router(schedule_router)
    dp.include_router(challenge_router)
    dp.include_router(equipment_router)
    dp.include_router(achievements_router)

    await dp.start_polling(bot, handle_signals=False)
    yield dp
    await dp.stop_polling()


# ── Seed data ──────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def seed_exercises(session: AsyncSession):
    """Create muscle groups + equipment + exercises for workout generation."""
    # Muscle groups (table, not enum)
    mgs = {
        "legs": MuscleGroup(code="legs", name_ru="Ноги", name_en="Legs", body_part="lower"),
        "chest": MuscleGroup(code="chest", name_ru="Грудь", name_en="Chest", body_part="upper"),
        "back": MuscleGroup(code="back", name_ru="Спина", name_en="Back", body_part="upper"),
        "shoulders": MuscleGroup(code="shoulders", name_ru="Плечи", name_en="Shoulders", body_part="upper"),
        "arms": MuscleGroup(code="arms", name_ru="Руки", name_en="Arms", body_part="upper"),
        "abs": MuscleGroup(code="abs", name_ru="Пресс", name_en="Abs", body_part="core"),
    }
    session.add_all(mgs.values())
    await session.flush()

    # Equipment items (table, not enum)
    eq = {
        "barbell": Equipment(code="barbell", name_ru="Штанга", name_en="Barbell",
                             category=EquipmentCategory.stationary, icon="🏋️"),
        "dumbbells": Equipment(code="dumbbells", name_ru="Гантели", name_en="Dumbbells",
                               category=EquipmentCategory.portable, icon="🏋️‍♂️"),
        "bench": Equipment(code="bench", name_ru="Скамья", name_en="Bench",
                           category=EquipmentCategory.stationary, icon="🪑"),
        "bodyweight": Equipment(code="bodyweight", name_ru="Свой вес", name_en="Bodyweight",
                                category=EquipmentCategory.none, icon="🧘"),
        "pullup_bar": Equipment(code="pullup_bar", name_ru="Турник", name_en="Pull-up Bar",
                                category=EquipmentCategory.portable, icon="🔝"),
    }
    session.add_all(eq.values())
    await session.flush()

    exercises = [
        Exercise(
            code="barbell_squat", name_ru="Приседания со штангой", name_en="Barbell Squat",
            primary_muscle_group_id=mgs["legs"].id,
            required_equipment_id=eq["barbell"].id,
            equipment_category=EquipmentCategory.stationary,
            exercise_type=ExerciseType.compound,
            gif_url="https://ex.com/sq.gif",
        ),
        Exercise(
            code="bench_press", name_ru="Жим лёжа", name_en="Bench Press",
            primary_muscle_group_id=mgs["chest"].id,
            required_equipment_id=eq["barbell"].id,
            equipment_category=EquipmentCategory.stationary,
            exercise_type=ExerciseType.compound,
            gif_url="https://ex.com/bp.gif",
        ),
        Exercise(
            code="deadlift", name_ru="Становая тяга", name_en="Deadlift",
            primary_muscle_group_id=mgs["back"].id,
            required_equipment_id=eq["barbell"].id,
            equipment_category=EquipmentCategory.stationary,
            exercise_type=ExerciseType.compound,
            gif_url="https://ex.com/dl.gif",
        ),
        Exercise(
            code="pushups", name_ru="Отжимания", name_en="Push-ups",
            primary_muscle_group_id=mgs["chest"].id,
            required_equipment_id=eq["bodyweight"].id,
            equipment_category=EquipmentCategory.none,
            exercise_type=ExerciseType.compound,
            gif_url="https://ex.com/pu.gif",
        ),
        Exercise(
            code="pullups", name_ru="Подтягивания", name_en="Pull-ups",
            primary_muscle_group_id=mgs["back"].id,
            required_equipment_id=eq["pullup_bar"].id,
            equipment_category=EquipmentCategory.portable,
            exercise_type=ExerciseType.compound,
            gif_url="https://ex.com/pull.gif",
        ),
        Exercise(
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
    return exercises


@pytest_asyncio.fixture
async def registered_user(session: AsyncSession, seed_exercises):
    """A fully onboarded user with complete profile."""
    user = User(
        telegram_id=123456789,
        username="testuser",
        first_name="Тест",
        language="ru",
    )
    session.add(user)
    await session.flush()

    profile = Profile(
        user_id=user.id,
        gender="male",
        age=30,
        height_cm=180,
        weight_kg=80,
        goal="mass_gain",
        experience="intermediate",
        health_issues="none",
        equipment_category="stationary",
        equipment_items=["barbell", "dumbbells", "bench"],
        calibration_completed=True,
        calibration_date=date.today(),
    )
    session.add(profile)
    await session.flush()

    return user
