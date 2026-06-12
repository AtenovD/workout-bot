from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.reminder import Reminder
from core.database import get_session
from bot.keyboards.main_menu import main_menu_keyboard

router = Router()

DAYS_LABELS = {
    1: "🌞 Пн", 2: "🌞 Вт", 3: "🌞 Ср",
    4: "🌞 Чт", 5: "🌞 Пт", 6: "🌊 Сб", 7: "🌊 Вс"
}

REMINDER_DEFAULTS = {
    "workout":       {"time": "08:00", "desc": "🏋️ Напоминание о тренировке"},
    "weekly_report": {"time": "09:00", "desc": "📊 Еженедельный отчёт"},
    "motivation":    {"time": "10:00", "desc": "⚡ Мотивация при пропуске"},
}


class ReminderStates(StatesGroup):
    picking_type = State()
    picking_time = State()
    picking_days = State()


@router.callback_query(F.data == "menu:reminders")
@router.message(F.text == "🔔 Напоминания")
async def show_reminders(msg_or_cb, state: FSMContext, session: AsyncSession = None):
    if not session:
        session = await get_session()
    
    user_id = msg_or_cb.from_user.id
    text = msg_or_cb.message if isinstance(msg_or_cb, CallbackQuery) else msg_or_cb
    target = msg_or_cb.message if isinstance(msg_or_cb, CallbackQuery) else msg_or_cb

    # Load all reminders
    result = await session.execute(
        select(Reminder).where(Reminder.user_id == user_id)
    )
    existing = {r.type: r for r in result.scalars().all()}

    kb = InlineKeyboardBuilder()
    for rtype, info in REMINDER_DEFAULTS.items():
        r = existing.get(rtype)
        status = "✅ Вкл" if (r and r.enabled) else "❌ Выкл"
        kb.button(text=f"{info['desc']}: {status}", callback_data=f"remind:toggle:{rtype}")
    kb.button(text="◀️ Назад", callback_data="menu:main")
    kb.adjust(1)

    await target.answer(
        "🔔 <b>Напоминания</b>

"
        "Настрой уведомления:",
        reply_markup=kb.as_markup(), parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("remind:toggle:"))
async def toggle_reminder(cb: CallbackQuery, state: FSMContext, session: AsyncSession = None):
    if not session:
        session = await get_session()
    user_id = cb.from_user.id
    rtype = cb.data.split(":")[-1]

    result = await session.execute(
        select(Reminder).where(Reminder.user_id == user_id, Reminder.type == rtype)
    )
    existing = result.scalar()

    if existing:
        existing.enabled = not existing.enabled
    else:
        default_info = REMINDER_DEFAULTS.get(rtype, {})
        import datetime
        h, m = map(int, default_info.get("time", "08:00").split(":"))
        existing = Reminder(
            user_id=user_id, type=rtype,
            time_of_day=datetime.time(h, m),
            enabled=True
        )
        session.add(existing)

    await session.commit()

    # Re-render
    await show_reminders(cb, state, session)
    await cb.answer(
        f"✅ {REMINDER_DEFAULTS[rtype]['desc']}: {'Включено' if existing.enabled else 'Выключено'}"
    )
