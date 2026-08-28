from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
import json

from models.user import User
from models.workout import WorkoutSession, SessionStatus
from models.body_measurement import BodyMeasurement
from models.personal_record import PersonalRecord
from bot.keyboards.main_menu import main_menu_keyboard
from bot.services.subscription_gate import (
    get_required_en_channel,
    should_block_for_subscription,
    subscription_gate_markup,
    subscription_gate_text,
)
from bot.texts import t
from bot.utils.module_visuals import send_module_visual
from bot.utils.message_edit import safe_edit_text

router = Router()


@router.callback_query(F.data == "menu:settings")
@router.message(F.text.in_({"⚙️ Настройки", "⚙️ Settings"}))
async def settings_menu(msg_or_cb, user: User, **kwargs):
    lang = user.language_code or "ru"
    kb = InlineKeyboardBuilder()
    kb.button(text=t("settings_export", lang), callback_data="settings:export")
    kb.button(text=t("settings_reset", lang), callback_data="settings:reset_confirm")
    kb.button(text=t("settings_language", lang), callback_data="settings:language")
    kb.button(text=t("settings_main_menu", lang), callback_data="menu:main")
    kb.adjust(1)
    text = t("settings_title", lang)
    if isinstance(msg_or_cb, CallbackQuery):
        await send_module_visual(msg_or_cb, "settings", text, reply_markup=kb.as_markup())
    else:
        await send_module_visual(msg_or_cb, "settings", text, reply_markup=kb.as_markup())


@router.callback_query(F.data == "settings:language")
async def change_language(cb: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
    ], [InlineKeyboardButton(text="◀️", callback_data="menu:settings")]])
    await safe_edit_text(cb.message, t("language_choose"), reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data.startswith("lang:"))
async def save_language(cb: CallbackQuery, user: User, session: AsyncSession):
    language_code = cb.data.split(":", 1)[1]
    if language_code not in {"ru", "en"}:
        await cb.answer("Unsupported language", show_alert=True)
        return

    user.language_code = language_code
    await session.commit()

    if await should_block_for_subscription(cb.bot, session, user):
        channel = await get_required_en_channel(session)
        if channel:
            await safe_edit_text(
                cb.message,
                subscription_gate_text(channel),
                reply_markup=subscription_gate_markup(channel),
                parse_mode="HTML",
            )
        await cb.answer()
        return

    labels = {"ru": "Русский", "en": "English"}
    await safe_edit_text(cb.message,
        t("language_changed", language_code, language=labels[language_code]),
        reply_markup=main_menu_keyboard(lang=language_code, telegram_id=user.telegram_id),
        parse_mode="HTML",
    )
    await cb.answer()

@router.callback_query(F.data == "settings:export")
async def export_data(cb: CallbackQuery, user: User, session: AsyncSession):
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
        "personal_records": [
            {
                "exercise_id": pr.exercise_id,
                "record_type": pr.record_type,
                "value": float(pr.value),
                "achieved_at": str(pr.achieved_at),
            }
            for pr in prs
        ],
        "measurements": [{"date": str(m.recorded_at), "weight_kg": m.weight_kg} for m in measurements],
    }
    payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    await cb.message.answer_document(
        BufferedInputFile(payload, filename="my_workout_data.json"),
        caption="📤 Ваши данные",
    )
    await cb.answer()


@router.callback_query(F.data == "settings:reset_confirm")
async def reset_confirm(cb: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⚠️ Да, сбросить всё", callback_data="settings:reset_do"),
        InlineKeyboardButton(text="◀️ Отмена", callback_data="menu:settings"),
    ]])
    await safe_edit_text(cb.message,
        "⚠️ <b>Подтверждение сброса</b>\n\n"
        "Это удалит все твои тренировки, рекорды и измерения. Отменить нельзя.\n\n"
        "Ты уверен?",
        reply_markup=kb, parse_mode="HTML"
    )


@router.callback_query(F.data == "settings:reset_do")
async def reset_do(cb: CallbackQuery, user: User, session: AsyncSession):
    await session.execute(delete(WorkoutSession).where(WorkoutSession.user_id == user.id))
    await session.execute(delete(PersonalRecord).where(PersonalRecord.user_id == user.id))
    await session.execute(delete(BodyMeasurement).where(BodyMeasurement.user_id == user.id))
    await session.commit()
    await safe_edit_text(cb.message,
        "🗑 <b>Прогресс сброшен.</b>\n\nВсе тренировки, рекорды и замеры удалены.",
        reply_markup=main_menu_keyboard(lang=user.language_code or "ru", telegram_id=user.telegram_id),
        parse_mode="HTML"
    )
