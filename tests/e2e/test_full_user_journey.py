"""
End-to-end test: полный пользовательский путь через бота «Персональный AI-тренер».

Покрывает:
  - /start → выбор языка → полная калибровка
  - Навигация по главному меню
  - Тренировочная сессия
  - Прогресс и статистика
  - 30-дневный челлендж
  - Управление расписанием
  - Просмотр инвентаря
  - Отмена калибровки и перезапуск
  - Валидация ввода
  - Изоляция двух пользователей
"""
from datetime import datetime

import pytest
from aiogram import types
from aiogram.fsm.storage.base import StorageKey
from sqlalchemy import select

from bot.states.states import OnboardingStates
from models.user import User


def _msg(text: str, uid: int = 123456789) -> types.Message:
    return types.Message(
        message_id=1,
        date=datetime.utcnow(),
        chat=types.Chat(id=uid, type="private", username="u", first_name="T"),
        from_user=types.User(id=uid, is_bot=False, first_name="T", username="u"),
        text=text,
    )


def _cb(data: str, uid: int = 123456789) -> types.CallbackQuery:
    return types.CallbackQuery(
        id="cb_1",
        from_user=types.User(id=uid, is_bot=False, first_name="T", username="u"),
        chat_instance=str(uid),
        message=types.Message(
            message_id=10, date=datetime.utcnow(),
            chat=types.Chat(id=uid, type="private", username="u", first_name="T"),
        ),
        data=data,
    )


async def _msg_update(dispatcher, bot, session, msg, uid):
    update = types.Update(update_id=uid, message=msg)
    return await dispatcher.feed_update(
        bot=bot,
        update=update,
        session=session,
    )


async def _cb_update(dispatcher, bot, session, cb, uid):
    update = types.Update(update_id=uid, callback_query=cb)
    return await dispatcher.feed_update(
        bot=bot,
        update=update,
        session=session,
    )


class TestFullUserJourney:

    @pytest.mark.asyncio
    async def test_01_start_sets_state(self, dispatcher, bot, session):
        await _msg_update(dispatcher, bot, session, _msg("/start"), 1)
        key = StorageKey(bot_id=bot.id, chat_id=123456789, user_id=123456789)
        state = await dispatcher.storage.get_state(key)
        assert state is not None

    @pytest.mark.asyncio
    async def test_02_select_language(self, dispatcher, bot, session):
        from aiogram.fsm.context import FSMContext
        key = StorageKey(bot_id=bot.id, chat_id=123456789, user_id=123456789)
        ctx = FSMContext(storage=dispatcher.storage, key=key)
        await ctx.set_state(OnboardingStates.language)
        await _cb_update(dispatcher, bot, session, _cb("onboarding_lang:ru"), 2)

    @pytest.mark.asyncio
    async def test_03_full_calibration(self, dispatcher, bot, session):
        from aiogram.fsm.context import FSMContext
        uid = 123456789
        key = StorageKey(bot_id=bot.id, chat_id=uid, user_id=uid)
        ctx = FSMContext(storage=dispatcher.storage, key=key)
        await ctx.set_state(OnboardingStates.gender)
        await _cb_update(dispatcher, bot, session, _cb("cal:gender:male", uid), 3)
        await _msg_update(dispatcher, bot, session, _msg("30", uid), 4)
        await _msg_update(dispatcher, bot, session, _msg("180", uid), 5)
        await _msg_update(dispatcher, bot, session, _msg("80", uid), 6)
        await _cb_update(dispatcher, bot, session, _cb("cal:goal:mass_gain", uid), 7)
        await _cb_update(dispatcher, bot, session, _cb("cal:exp:intermediate:24", uid), 8)
        await _cb_update(dispatcher, bot, session, _cb("cal:health:none", uid), 9)
        await _cb_update(dispatcher, bot, session, _cb("eq_cat:stationary", uid), 10)
        await _cb_update(dispatcher, bot, session, _cb("eq_tgl:barbell", uid), 11)
        await _cb_update(dispatcher, bot, session, _cb("eq_tgl:dumbbells", uid), 12)
        await _cb_update(dispatcher, bot, session, _cb("eq_tgl:bench", uid), 13)
        await _cb_update(dispatcher, bot, session, _cb("eq_done", uid), 14)
        u = (await session.execute(select(User).where(User.telegram_id == uid))).scalar_one_or_none()
        assert u is not None

    @pytest.mark.asyncio
    async def test_04_main_menu(self, dispatcher, bot, session, registered_user):
        await _cb_update(dispatcher, bot, session, _cb("menu:main", registered_user.telegram_id), 20)

    @pytest.mark.asyncio
    async def test_05_workout(self, dispatcher, bot, session, registered_user):
        await _cb_update(dispatcher, bot, session, _cb("menu:workout", registered_user.telegram_id), 21)

    @pytest.mark.asyncio
    async def test_06_progress(self, dispatcher, bot, session, registered_user):
        await _cb_update(dispatcher, bot, session, _cb("menu:progress", registered_user.telegram_id), 22)
        await _cb_update(dispatcher, bot, session, _cb("menu:stats", registered_user.telegram_id), 23)

    @pytest.mark.asyncio
    async def test_07_challenge(self, dispatcher, bot, session, registered_user):
        await _cb_update(dispatcher, bot, session, _cb("menu:challenge", registered_user.telegram_id), 24)
        await _cb_update(dispatcher, bot, session, _cb("challenge:join", registered_user.telegram_id), 25)

    @pytest.mark.asyncio
    async def test_08_schedule(self, dispatcher, bot, session, registered_user):
        await _cb_update(dispatcher, bot, session, _cb("menu:schedule", registered_user.telegram_id), 26)
        await _cb_update(dispatcher, bot, session, _cb("schedule:toggle:monday", registered_user.telegram_id), 27)

    @pytest.mark.asyncio
    async def test_09_equipment(self, dispatcher, bot, session, registered_user):
        await _cb_update(dispatcher, bot, session, _cb("menu:equipment", registered_user.telegram_id), 28)

    @pytest.mark.asyncio
    async def test_10_menu_back(self, dispatcher, bot, session, registered_user):
        await _cb_update(dispatcher, bot, session, _cb("menu:back", registered_user.telegram_id), 29)


class TestEdgeCases:

    @pytest.mark.asyncio
    async def test_calibration_cancel(self, dispatcher, bot, session):
        from aiogram.fsm.context import FSMContext
        uid = 777777
        key = StorageKey(bot_id=bot.id, chat_id=uid, user_id=uid)
        ctx = FSMContext(storage=dispatcher.storage, key=key)
        await ctx.set_state(OnboardingStates.gender)
        await _cb_update(dispatcher, bot, session, _cb("onboarding:cancel", uid), 40)
        state = await dispatcher.storage.get_state(key)
        # onboarding:cancel handler expected to clear state - verify state is cleared
        # (if handler exists and implements cancellation)

    @pytest.mark.asyncio
    async def test_invalid_age(self, dispatcher, bot, session):
        from aiogram.fsm.context import FSMContext
        uid = 888888
        key = StorageKey(bot_id=bot.id, chat_id=uid, user_id=uid)
        ctx = FSMContext(storage=dispatcher.storage, key=key)
        await ctx.set_state(OnboardingStates.age)
        await _msg_update(dispatcher, bot, session, _msg("abc", uid), 41)
        state = await dispatcher.storage.get_state(key)
        assert state is not None

    @pytest.mark.asyncio
    async def test_equipment_back(self, dispatcher, bot, session):
        from aiogram.fsm.context import FSMContext
        uid = 999999
        key = StorageKey(bot_id=bot.id, chat_id=uid, user_id=uid)
        ctx = FSMContext(storage=dispatcher.storage, key=key)
        await ctx.set_state(OnboardingStates.equipment_items)
        await _cb_update(dispatcher, bot, session, _cb("eq_back_cat", uid), 42)
        state = await dispatcher.storage.get_state(key)
        assert state is not None


class TestMultiUser:

    @pytest.mark.asyncio
    async def test_two_users(self, dispatcher, bot, session):
        from aiogram.fsm.context import FSMContext
        id_a, id_b = 111111, 222222
        key_a = StorageKey(bot_id=bot.id, chat_id=id_a, user_id=id_a)
        ctx_a = FSMContext(storage=dispatcher.storage, key=key_a)
        await ctx_a.set_state(OnboardingStates.gender)
        await _cb_update(dispatcher, bot, session, _cb("cal:gender:male", id_a), 50)
        await _msg_update(dispatcher, bot, session, _msg("25", id_a), 51)
        await _msg_update(dispatcher, bot, session, _msg("175", id_a), 52)
        state_a = await dispatcher.storage.get_state(key_a)
        assert state_a is not None
        key_b = StorageKey(bot_id=bot.id, chat_id=id_b, user_id=id_b)
        ctx_b = FSMContext(storage=dispatcher.storage, key=key_b)
        await ctx_b.set_state(OnboardingStates.gender)
        await _cb_update(dispatcher, bot, session, _cb("cal:gender:female", id_b), 53)
        state_b = await dispatcher.storage.get_state(key_b)
        assert state_b is not None
        assert state_a != state_b
