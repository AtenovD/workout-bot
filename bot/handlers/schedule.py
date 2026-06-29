from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from datetime import time

from models.user import User
from models.schedule import Schedule, ScheduleMode
from bot.states.states import ScheduleStates
from bot.utils.module_visuals import send_module_visual
from bot.utils.message_edit import safe_edit_text

router = Router()

DAY_NAMES = {0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс"}
DAY_ALIASES = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def schedule_menu_kb(schedule=None):
    rows = []
    if schedule and schedule.mode == ScheduleMode.fixed:
        days = schedule.days_of_week or []
        day_row = []
        for d in range(7):
            mark = "✅" if d in days else "⬜"
            day_row.append(InlineKeyboardButton(text=f"{mark}{DAY_NAMES[d]}", callback_data=f"schedule:day:{d}"))
        rows.append(day_row[:4])
        rows.append(day_row[4:])
        rem_text = f"🔔 Напоминание: {'вкл' if schedule.reminder_enabled else 'выкл'}"
        rows.append([InlineKeyboardButton(text=rem_text, callback_data="schedule:toggle_reminder")])
        if schedule.reminder_enabled:
            time_str = schedule.reminder_time.strftime("%H:%M") if schedule.reminder_time else "не задано"
            rows.append([InlineKeyboardButton(text=f"⏰ Время: {time_str}", callback_data="schedule:set_time")])
    else:
        rows.append([
            InlineKeyboardButton(text="📅 Фиксированный", callback_data="schedule:mode:fixed"),
            InlineKeyboardButton(text="🎲 Спонтанный", callback_data="schedule:mode:spontaneous"),
        ])
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="menu:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _create_schedule(session: AsyncSession, user_id: int, mode: ScheduleMode = ScheduleMode.spontaneous) -> Schedule:
    max_id = (await session.execute(select(func.max(Schedule.id)))).scalar() or 0
    sched = Schedule(id=max_id + 1, user_id=user_id, mode=mode)
    session.add(sched)
    return sched


@router.message(Command("schedule"))
@router.callback_query(F.data == "menu:schedule")
async def show_schedule(event, user: User, session: AsyncSession, **kwargs):
    msg = event.message if isinstance(event, CallbackQuery) else event
    sched_res = await session.execute(select(Schedule).where(Schedule.user_id == user.id))
    sched = sched_res.scalar_one_or_none()

    if not sched:
        text = "📅 <b>Расписание</b>\n\nВыбери режим тренировок:"
    else:
        mode_names = {"fixed": "Фиксированный", "spontaneous": "Спонтанный"}
        days = sched.days_of_week or []
        days_str = ", ".join(DAY_NAMES[d] for d in sorted(days)) if days else "не выбраны"
        text = (
            f"📅 <b>Расписание</b>\n\n"
            f"Режим: {mode_names.get(sched.mode.value, '—')}\n"
            f"Дни: {days_str}\n"
            f"Напоминание: {'✅ вкл' if sched.reminder_enabled else '❌ выкл'}"
        )
        if sched.reminder_enabled and sched.reminder_time:
            text += f"\nВремя: {sched.reminder_time.strftime('%H:%M')}"

    await send_module_visual(event, "schedule", text, reply_markup=schedule_menu_kb(sched))
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.callback_query(F.data.startswith("sched:mode:"))
@router.callback_query(F.data.startswith("schedule:mode:"))
async def set_mode(callback: CallbackQuery, user: User, session: AsyncSession):
    mode = callback.data.split(":")[2]
    sched_res = await session.execute(select(Schedule).where(Schedule.user_id == user.id))
    sched = sched_res.scalar_one_or_none()
    if not sched:
        sched = await _create_schedule(session, user.id)
    sched.mode = ScheduleMode(mode)
    await session.commit()
    await show_schedule(callback, user=user, session=session)


@router.callback_query(F.data.startswith("sched:day:"))
@router.callback_query(F.data.startswith("schedule:day:"))
@router.callback_query(F.data.startswith("schedule:toggle:"))
async def toggle_day(callback: CallbackQuery, user: User, session: AsyncSession):
    raw_day = callback.data.split(":")[2]
    day = DAY_ALIASES.get(raw_day, int(raw_day) if raw_day.isdigit() else -1)
    if day not in DAY_NAMES:
        await callback.answer("Неизвестный день.", show_alert=True)
        return
    sched_res = await session.execute(select(Schedule).where(Schedule.user_id == user.id))
    sched = sched_res.scalar_one_or_none()
    if not sched:
        sched = await _create_schedule(session, user.id, ScheduleMode.fixed)
        await session.flush()
    if sched.mode != ScheduleMode.fixed:
        sched.mode = ScheduleMode.fixed
    days = list(sched.days_of_week or [])
    if day in days:
        days.remove(day)
    else:
        days.append(day)
    sched.days_of_week = sorted(days)
    await session.commit()
    await show_schedule(callback, user=user, session=session)


@router.callback_query(F.data == "sched:toggle_reminder")
@router.callback_query(F.data == "schedule:toggle_reminder")
async def toggle_reminder(callback: CallbackQuery, user: User, session: AsyncSession):
    sched_res = await session.execute(select(Schedule).where(Schedule.user_id == user.id))
    sched = sched_res.scalar_one_or_none()
    if sched:
        sched.reminder_enabled = not sched.reminder_enabled
        await session.commit()
    await show_schedule(callback, user=user, session=session)


@router.callback_query(F.data == "sched:set_time")
@router.callback_query(F.data == "schedule:set_time")
async def ask_reminder_time(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ScheduleStates.entering_time)
    await safe_edit_text(callback.message, "Введи время напоминания в формате ЧЧ:ММ\n_Например: 08:00_", parse_mode="Markdown")
    await callback.answer()


@router.message(ScheduleStates.entering_time, F.text)
async def save_reminder_time(message: Message, state: FSMContext, user: User, session: AsyncSession):
    try:
        h, m = message.text.split(":")
        t = time(int(h), int(m))
    except Exception:
        await message.answer("Неверный формат. Введи в виде ЧЧ:ММ, например 08:00")
        return
    sched_res = await session.execute(select(Schedule).where(Schedule.user_id == user.id))
    sched = sched_res.scalar_one_or_none()
    if sched:
        sched.reminder_time = t
        await session.commit()
    await state.clear()
    await message.answer(f"✅ Время напоминания установлено: {t.strftime('%H:%M')}")
