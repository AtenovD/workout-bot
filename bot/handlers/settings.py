from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
import json, io

from models.user import User
from models.workout_session import WorkoutSession
from models.body_measurement import BodyMeasurement
from models.personal_record import PersonalRecord
from core.database import get_session
from bot.keyboards.main_menu import main_menu_keyboard

router = Router()


@router.callback_query(F.data == "menu:settings")
@router.message(F.text == "\u2699\ufe0f \u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438")
async def settings_menu(msg_or_cb, session: AsyncSession = None):
    if not session:
        session = await get_session()
    target = msg_or_cb.message if isinstance(msg_or_cb, CallbackQuery) else msg_or_cb
    kb = InlineKeyboardBuilder()
    kb.button(text="\ud83d\udce4 \u042d\u043a\u0441\u043f\u043e\u0440\u0442 \u0434\u0430\u043d\u043d\u044b\u0445",   callback_data="settings:export")
    kb.button(text="\ud83d\uddd1\ufe0f \u0421\u0431\u0440\u043e\u0441\u0438\u0442\u044c \u043f\u0440\u043e\u0433\u0440\u0435\u0441\u0441", callback_data="settings:reset_confirm")
    kb.button(text="\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434",             callback_data="menu:main")
    kb.adjust(1)
    await target.answer("\u2699\ufe0f <b>\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438</b>\n\n\u0412\u044b\u0431\u0435\u0440\u0438 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0435:",
                        reply_markup=kb.as_markup(), parse_mode="HTML")


@router.callback_query(F.data == "settings:export")
async def export_data(cb: CallbackQuery, session: AsyncSession = None):
    if not session:
        session = await get_session()
    user_id = cb.from_user.id
    await cb.answer("\u0424\u043e\u0440\u043c\u0438\u0440\u0443\u044e...")

    def row_to_dict(obj):
        return {c.name: str(getattr(obj, c.name)) for c in obj.__table__.columns}

    ws  = (await session.execute(select(WorkoutSession).where(WorkoutSession.user_id == user_id))).scalars().all()
    bm  = (await session.execute(select(BodyMeasurement).where(BodyMeasurement.user_id == user_id))).scalars().all()
    pr  = (await session.execute(select(PersonalRecord).where(PersonalRecord.user_id == user_id))).scalars().all()

    data = {"workouts": [row_to_dict(r) for r in ws],
            "measurements": [row_to_dict(r) for r in bm],
            "records": [row_to_dict(r) for r in pr]}
    buf = io.BytesIO(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
    buf.name = "my_workout_data.json"
    await cb.message.answer_document(buf, caption="\ud83d\udce4 \u0422\u0432\u043e\u0438 \u0434\u0430\u043d\u043d\u044b\u0435 \u044d\u043a\u0441\u043f\u043e\u0440\u0442\u0438\u0440\u043e\u0432\u0430\u043d\u044b.")


@router.callback_query(F.data == "settings:reset_confirm")
async def reset_confirm(cb: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="\u26a0\ufe0f \u0414\u0430, \u0441\u0431\u0440\u043e\u0441\u0438\u0442\u044c \u0432\u0441\u0451", callback_data="settings:reset_do")
    kb.button(text="\u25c0\ufe0f \u041e\u0442\u043c\u0435\u043d\u0430",           callback_data="menu:settings")
    kb.adjust(1)
    await cb.message.edit_text(
        "\u26a0\ufe0f <b>\u0421\u0431\u0440\u043e\u0441 \u043f\u0440\u043e\u0433\u0440\u0435\u0441\u0441\u0430</b>\n\n"
        "\u0411\u0443\u0434\u0443\u0442 \u0443\u0434\u0430\u043b\u0435\u043d\u044b \u0432\u0441\u0435 \u0442\u0440\u0435\u043d\u0438\u0440\u043e\u0432\u043a\u0438, \u0440\u0435\u043a\u043e\u0440\u0434\u044b \u0438 \u0437\u0430\u043c\u0435\u0440\u044b.\n<b>\u042d\u0442\u043e \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0435 \u043d\u0435\u043e\u0431\u0440\u0430\u0442\u0438\u043c\u043e!</b>",
        reply_markup=kb.as_markup(), parse_mode="HTML")


@router.callback_query(F.data == "settings:reset_do")
async def reset_do(cb: CallbackQuery, session: AsyncSession = None):
    if not session:
        session = await get_session()
    uid = cb.from_user.id
    await cb.answer()
    for Model in [WorkoutSession, BodyMeasurement, PersonalRecord]:
        await session.execute(delete(Model).where(Model.user_id == uid))
    await session.commit()
    await cb.message.edit_text(
        "\u2705 \u041f\u0440\u043e\u0433\u0440\u0435\u0441\u0441 \u0441\u0431\u0440\u043e\u0448\u0435\u043d. \u041d\u0430\u0447\u0438\u043d\u0430\u0435\u043c \u0441 \u0447\u0438\u0441\u0442\u043e\u0433\u043e \u043b\u0438\u0441\u0442\u0430! \ud83d\udcaa",
        reply_markup=main_menu_keyboard())
