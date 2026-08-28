from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.main_menu import main_menu_keyboard
from bot.utils.message_edit import safe_edit_text
from core.database import get_session
from models.body_measurement import BodyMeasurement
from models.user import User

router = Router()

MEASURE_LABELS = {
    "ru": {
        "weight_kg": "⚖️ Вес (кг)",
        "chest_cm": "💪 Грудь (см)",
        "waist_cm": "📏 Талия (см)",
        "hips_cm": "🧍 Бедра (см)",
        "biceps_left_cm": "💪 Левый бицепс (см)",
        "biceps_right_cm": "💪 Правый бицепс (см)",
        "thigh_left_cm": "🦵 Левое бедро (см)",
        "thigh_right_cm": "🦵 Правое бедро (см)",
        "neck_cm": "👔 Шея (см)",
        "bodyfat_pct": "📊 Жир (%)",
    },
    "en": {
        "weight_kg": "⚖️ Weight (kg)",
        "chest_cm": "💪 Chest (cm)",
        "waist_cm": "📏 Waist (cm)",
        "hips_cm": "🧍 Hips (cm)",
        "biceps_left_cm": "💪 Left biceps (cm)",
        "biceps_right_cm": "💪 Right biceps (cm)",
        "thigh_left_cm": "🦵 Left thigh (cm)",
        "thigh_right_cm": "🦵 Right thigh (cm)",
        "neck_cm": "👔 Neck (cm)",
        "bodyfat_pct": "📊 Body fat (%)",
    },
}

MEASURE_ORDER = [
    "weight_kg",
    "chest_cm",
    "waist_cm",
    "hips_cm",
    "biceps_left_cm",
    "biceps_right_cm",
    "thigh_left_cm",
    "thigh_right_cm",
    "neck_cm",
    "bodyfat_pct",
]


class MeasureStates(StatesGroup):
    entering = State()


def _lang(user: User | None = None) -> str:
    return "en" if user and user.language_code == "en" else "ru"


def _measure_kb(lang: str, has_history: bool) -> InlineKeyboardMarkup:
    if lang == "en":
        rows = [[InlineKeyboardButton(text="📝 Add measurement", callback_data="meas:new")]]
        if has_history:
            rows.append([InlineKeyboardButton(text="📊 History", callback_data="meas:history")])
        rows.extend([
            [InlineKeyboardButton(text="◀️ Back to progress", callback_data="menu:progress")],
            [InlineKeyboardButton(text="🏠 Main menu", callback_data="menu:main")],
        ])
    else:
        rows = [[InlineKeyboardButton(text="📝 Добавить замер", callback_data="meas:new")]]
        if has_history:
            rows.append([InlineKeyboardButton(text="📊 История", callback_data="meas:history")])
        rows.extend([
            [InlineKeyboardButton(text="◀️ Назад к прогрессу", callback_data="menu:progress")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")],
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _after_save_kb(lang: str) -> InlineKeyboardMarkup:
    if lang == "en":
        rows = [
            [InlineKeyboardButton(text="📊 Measurements", callback_data="menu:measurements")],
            [InlineKeyboardButton(text="◀️ Back to progress", callback_data="menu:progress")],
        ]
    else:
        rows = [
            [InlineKeyboardButton(text="📊 Замеры тела", callback_data="menu:measurements")],
            [InlineKeyboardButton(text="◀️ Назад к прогрессу", callback_data="menu:progress")],
        ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _measurement_lines(measurement: BodyMeasurement, lang: str) -> list[str]:
    labels = MEASURE_LABELS[lang]
    lines = []
    date_str = measurement.recorded_at.strftime("%d.%m.%Y") if measurement.recorded_at else "—"
    lines.append(f"📅 <i>{date_str}</i>")
    for field in MEASURE_ORDER:
        value = getattr(measurement, field, None)
        if value is not None:
            lines.append(f"{labels[field]}: <b>{float(value):g}</b>")
    return lines


@router.callback_query(F.data == "menu:measurements")
async def measurements_menu(callback: CallbackQuery, state: FSMContext, user: User, session: AsyncSession = None):
    if not session:
        session = await get_session()
    lang = _lang(user)
    await state.clear()

    latest = (
        await session.execute(
            select(BodyMeasurement)
            .where(BodyMeasurement.user_id == user.telegram_id)
            .order_by(desc(BodyMeasurement.recorded_at))
            .limit(1)
        )
    ).scalar_one_or_none()

    if latest:
        title = "📏 <b>Latest body measurement</b>\n" if lang == "en" else "📏 <b>Последние замеры тела</b>\n"
        text = title + "\n".join(_measurement_lines(latest, lang))
    elif lang == "en":
        text = (
            "📏 <b>Body measurements</b>\n\n"
            "No measurements yet. Add weight, waist, chest or other values once in a while — then the weight chart and progress screen become useful."
        )
    else:
        text = (
            "📏 <b>Замеры тела</b>\n\n"
            "Записей пока нет. Добавляй вес, талию, грудь и другие значения время от времени — тогда график веса и экран прогресса станут полезнее."
        )

    await safe_edit_text(callback.message, text, reply_markup=_measure_kb(lang, bool(latest)), parse_mode="HTML")
    await callback.answer()


@router.message(F.text == "📏 Замеры")
async def measurements_menu_legacy(message: Message, state: FSMContext, user: User, session: AsyncSession = None):
    if not session:
        session = await get_session()
    lang = _lang(user)
    await state.clear()
    latest = (
        await session.execute(
            select(BodyMeasurement)
            .where(BodyMeasurement.user_id == user.telegram_id)
            .order_by(desc(BodyMeasurement.recorded_at))
            .limit(1)
        )
    ).scalar_one_or_none()
    if latest:
        text = ("📏 <b>Latest body measurement</b>\n" if lang == "en" else "📏 <b>Последние замеры тела</b>\n") + "\n".join(
            _measurement_lines(latest, lang)
        )
    else:
        text = (
            "📏 <b>Body measurements</b>\n\nNo measurements yet."
            if lang == "en"
            else "📏 <b>Замеры тела</b>\n\nЗаписей пока нет."
        )
    await message.answer(text, reply_markup=_measure_kb(lang, bool(latest)), parse_mode="HTML")


@router.callback_query(F.data == "meas:new")
async def start_new_measurement(callback: CallbackQuery, state: FSMContext, user: User):
    lang = _lang(user)
    await state.set_state(MeasureStates.entering)
    await state.update_data(steps={}, current_idx=0, language=lang)
    field = MEASURE_ORDER[0]
    if lang == "en":
        text = (
            "📏 <b>New measurement</b>\n\n"
            f"{MEASURE_LABELS[lang][field]}:\n"
            "<i>Enter a number, or type skip</i>"
        )
    else:
        text = (
            "📏 <b>Новый замер</b>\n\n"
            f"{MEASURE_LABELS[lang][field]}:\n"
            "<i>Введи число или напиши «пропустить»</i>"
        )
    await safe_edit_text(callback.message, text, parse_mode="HTML")
    await callback.answer()


@router.message(MeasureStates.entering, F.text)
async def process_measure_step(message: Message, state: FSMContext, user: User, session: AsyncSession = None):
    if not session:
        session = await get_session()
    data = await state.get_data()
    lang = data.get("language") or _lang(user)
    steps = data.get("steps", {})
    idx = data.get("current_idx", 0)
    field = MEASURE_ORDER[idx]

    raw = message.text.strip().lower().replace(",", ".")
    skip_words = {"skip", "-", "пропустить", "пропуск"}
    if raw not in skip_words:
        try:
            steps[field] = float(raw)
        except ValueError:
            text = "❌ Enter a number or type skip" if lang == "en" else "❌ Введи число или «пропустить»"
            await message.answer(text)
            return

    next_idx = idx + 1
    if next_idx < len(MEASURE_ORDER):
        await state.update_data(steps=steps, current_idx=next_idx)
        next_field = MEASURE_ORDER[next_idx]
        text = (
            f"{MEASURE_LABELS[lang][next_field]}:\n<i>Enter a number, or type skip</i>"
            if lang == "en"
            else f"{MEASURE_LABELS[lang][next_field]}:\n<i>Введи число или напиши «пропустить»</i>"
        )
        await message.answer(text, parse_mode="HTML")
        return

    await state.update_data(steps=steps)
    await save_measurement(message, state, session, user, steps, lang)


async def save_measurement(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    user: User,
    steps: dict,
    lang: str,
):
    if not steps:
        await state.clear()
        text = "No values entered." if lang == "en" else "Не введено ни одного значения."
        await message.answer(text, reply_markup=_after_save_kb(lang))
        return

    measurement = BodyMeasurement(user_id=user.telegram_id, **steps, recorded_at=datetime.utcnow())
    session.add(measurement)
    await session.commit()
    await state.clear()

    title = "✅ <b>Measurement saved!</b>\n" if lang == "en" else "✅ <b>Замеры сохранены!</b>\n"
    lines = [title, *_measurement_lines(measurement, lang)]
    await message.answer("\n".join(lines), reply_markup=_after_save_kb(lang), parse_mode="HTML")


@router.callback_query(F.data == "meas:history")
async def measurement_history(callback: CallbackQuery, user: User, session: AsyncSession = None):
    if not session:
        session = await get_session()
    lang = _lang(user)
    records = (
        await session.execute(
            select(BodyMeasurement)
            .where(BodyMeasurement.user_id == user.telegram_id)
            .order_by(desc(BodyMeasurement.recorded_at))
            .limit(10)
        )
    ).scalars().all()

    if not records:
        text = "📊 No measurements yet." if lang == "en" else "📊 Замеров пока нет."
        await safe_edit_text(callback.message, text, reply_markup=_measure_kb(lang, False), parse_mode="HTML")
        await callback.answer()
        return

    lines = ["📊 <b>Measurement history</b>\n" if lang == "en" else "📊 <b>История замеров</b>\n"]
    for record in records:
        date_str = record.recorded_at.strftime("%d.%m") if record.recorded_at else "—"
        weight = f"{record.weight_kg:g} kg" if record.weight_kg and lang == "en" else f"{record.weight_kg:g} кг" if record.weight_kg else "—"
        waist = f", waist {record.waist_cm:g} cm" if record.waist_cm and lang == "en" else f", талия {record.waist_cm:g} см" if record.waist_cm else ""
        lines.append(f"📅 {date_str} | ⚖️ {weight}{waist}")

    await safe_edit_text(callback.message, "\n".join(lines), reply_markup=_measure_kb(lang, True), parse_mode="HTML")
    await callback.answer()
