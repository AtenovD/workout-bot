from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
import json, io

from models.user import User
from models.workout import WorkoutSession, SessionStatus
from models.body_measurement import BodyMeasurement
from models.personal_record import PersonalRecord
from core.db import AsyncSessionLocal
from bot.keyboards.main_menu import main_menu_keyboard

router = Router()


@router.callback_query(F.data == "menu:settings")
@router.message(F.text == "⚙️ Настройки")
async def settings_menu(msg_or_cb, user: User, **kwargs):
    target = msg_or_cb.message if isinstance(msg_or_cb, CallbackQuery) else msg_or_cb
    kb = InlineKeyboardBuilder()
    kb.button(text="📤 Экспорт данных", callback_data="settings:export")
    kb.button(text="🗑 Сбросить прогресс", callback_data="settings:reset_confirm")
    kb.button(text="🌍 Сменить язык", callback_data="settings:language")
    kb.button(text="◀️ Главное меню", callback_data="menu:main")
    kb.adjust(1)
    text = "⚙️ <b>Настройки</b>\n\nВыберите действие:"
    if isinstance(msg_or_cb, CallbackQuery):
        await target.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")


@router.callback_query(F.data == "settings:language")
async def change_language(cb: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
    ], [InlineKeyboardButton(text="◀️", callback_data="menu:settings")]])
    await cb.message.edit_text("🌍 Choose language / Выберите язык:", reply_markup=kb)


@router.callback_query(F.data == "settings:export")
async def export_data(cb: CallbackQuery, user: User):
    async with AsyncSessionLocal() as session:
        sessions = (await session.execute(
            select(WorkoutSession).where(WorkoutSession.user_id == user.id)
        )).scalars().all()
        prs = (await session.execute(
            select(PersonalRecord).where(PersonalRecord.user_id == user.id)
        )).scalars().all()
        measurements = (await session.execute(
            select(BodyMeasurement).where(BodyMeasurement.user_id == user.id)
        )).scalars().all()

    data = {
        "sessions": [{"id": s.id, "status": s.status.value if s.status else None,
                      "created_at": str(s.created_at)} for s in sessions],
        "personal_records": [{"exercise_code": pr.exercise_code, "weight_kg": pr.weight_kg,
                               "reps": pr.reps} for pr in prs],
        "measurements": [{"date": str(m.date), "weight_kg": m.weight_kg} for m in measurements],
    }
    buf = io.BytesIO(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
    buf.name = "my_workout_data.json"
    await cb.message.answer_document(buf, caption="📤 Ваши данные")
    await cb.answer()


@router.callback_query(F.data == "settings:reset_confirm")
async def reset_confirm(cb: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⚠️ Да, сбросить всё", callback_data="settings:reset_do"),
        InlineKeyboardButton(text="◀️ Отмена", callback_data="menu:settings"),
    ]])
    await cb.message.edit_text(
        "⚠️ <b>Подтверждение сброса</b>\n\n"
        "Это удалит все твои тренировки, рекорды и измерения. Отменить нельзя.\n\n"
        "Ты уверен?",
        reply_markup=kb, parse_mode="HTML"
    )


@router.callback_query(F.data == "settings:reset_do")
async def reset_do(cb: CallbackQuery, user: User):
    async with AsyncSessionLocal() as session:
        await session.execute(delete(WorkoutSession).where(WorkoutSession.user_id == user.id))
        await session.execute(delete(PersonalRecord).where(PersonalRecord.user_id == user.id))
        await session.execute(delete(BodyMeasurement).where(BodyMeasurement.user_id == user.id))
        await session.commit()
    await cb.message.edit_text(
        "🗑 <b>Прогресс сброшен.</b>\n\nВсе тренировки, рекорды и замеры удалены.",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )
