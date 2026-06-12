from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime

from models.body_measurement import BodyMeasurement
from core.database import get_session

router = Router()

MEASURE_LABELS = {
    "weight_kg":       "⚖️ Вес (кг)",
    "chest_cm":        "💪 Грудь (см)",
    "waist_cm":        "📏 Талия (см)",
    "hips_cm":         "🖌️ Бёдра (см)",
    "biceps_left_cm":  "💪 L Бицепс (см)",
    "biceps_right_cm": "💪 R Бицепс (см)",
    "thigh_left_cm":   "🦵 L Бедро (см)",
    "thigh_right_cm":  "🦵 R Бедро (см)",
    "neck_cm":         "👔 Шея (см)",
    "bodyfat_pct":     "📊 % Жира",
}

MEASURE_ORDER = ["weight_kg", "chest_cm", "waist_cm", "hips_cm", "biceps_left_cm", "biceps_right_cm", "thigh_left_cm", "thigh_right_cm", "neck_cm", "bodyfat_pct"]


class MeasureStates(StatesGroup):
    entering = State()
    confirming = State()


@router.callback_query(F.data == "menu:measurements")
@router.message(F.text == "📏 Замеры")
async def measurements_menu(msg_or_cb, state: FSMContext, session: AsyncSession = None):
    if not session:
        session = await get_session()
    user_id = msg_or_cb.from_user.id
    target = msg_or_cb.message if isinstance(msg_or_cb, CallbackQuery) else msg_or_cb

    # Show latest measurement
    result = await session.execute(
        select(BodyMeasurement).where(BodyMeasurement.user_id == user_id)
        .order_by(desc(BodyMeasurement.recorded_at)).limit(1)
    )
    latest = result.scalar()

    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Внести замеры", callback_data="meas:new")
    if latest:
        kb.button(text="📊 История", callback_data="meas:history")
    kb.button(text="◀️ Назад", callback_data="menu:main")
    kb.adjust(1)

    if latest:
        lines = ["📏 <b>Последние замеры</b>
"]
        date_str = latest.recorded_at.strftime("%d.%m.%Y") if latest.recorded_at else "—"
        lines.append(f"📅 <i>{date_str}</i>
")
        for field in MEASURE_ORDER:
            val = getattr(latest, field, None)
            if val is not None:
                lines.append(f"{MEASURE_LABELS[field]}: <b>{val}</b>")
        text = "
".join(lines)
    else:
        text = "📏 <b>Замеры тела</b>

Пока нет записей. Нажми «Внести замеры»."

    await target.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")


@router.callback_query(F.data == "meas:new")
async def start_new_measurement(cb: CallbackQuery, state: FSMContext):
    await state.set_state(MeasureStates.entering)
    await state.update_data(steps={}, current_idx=0)

    field = MEASURE_ORDER[0]
    await cb.message.edit_text(
        f"📏 <b>Новый замер</b>

"
        f"{MEASURE_LABELS[field]}:
"
        f"<i>Введи число или напиши «пропустить»</i>",
        parse_mode="HTML"
    )


@router.message(MeasureStates.entering, F.text)
async def process_measure_step(msg: Message, state: FSMContext, session: AsyncSession = None):
    if not session:
        session = await get_session()
    data = await state.get_data()
    steps = data.get("steps", {})
    idx = data.get("current_idx", 0)
    field = MEASURE_ORDER[idx]

    text = msg.text.strip().lower().replace(",", ".")
    if text in ("пропустить", "пропуск", "skip", "-"):
        # skip this field
        pass
    else:
        try:
            val = float(text)
            steps[field] = val
        except ValueError:
            await msg.answer(
                "❌ Введи число или «пропустить»",
                reply_markup=None
            )
            return

    next_idx = idx + 1
    if next_idx < len(MEASURE_ORDER):
        await state.update_data(steps=steps, current_idx=next_idx)
        next_field = MEASURE_ORDER[next_idx]
        await msg.answer(
            f"{MEASURE_LABELS[next_field]}:
<i>Введи число или «пропустить»</i>",
            parse_mode="HTML"
        )
    else:
        # All done — save
        await state.update_data(steps=steps)
        await save_measurement(msg, state, session, steps)


async def save_measurement(msg: Message, state: FSMContext, session: AsyncSession, steps: dict):
    user_id = msg.from_user.id
    m = BodyMeasurement(user_id=user_id, **steps, recorded_at=datetime.utcnow())
    session.add(m)
    await session.commit()
    await state.clear()

    # Build confirmation message
    lines = ["✅ <b>Замеры сохранены!</b>
"]
    for field in MEASURE_ORDER:
        if field in steps:
            lines.append(f"{MEASURE_LABELS[field]}: <b>{steps[field]}</b>")
    lines.append(f"
📅 {datetime.utcnow().strftime('%d.%m.%Y')}")

    await msg.answer("
".join(lines), reply_markup=main_menu_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "meas:history")
async def measurement_history(cb: CallbackQuery, session: AsyncSession = None):
    if not session:
        session = await get_session()
    user_id = cb.from_user.id

    result = await session.execute(
        select(BodyMeasurement).where(BodyMeasurement.user_id == user_id)
        .order_by(desc(BodyMeasurement.recorded_at)).limit(10)
    )
    records = result.scalars().all()

    if not records:
        await cb.message.edit_text(
            "📊 Замеров пока нет.",
            reply_markup=InlineKeyboardBuilder().button(text="◀️ Назад", callback_data="menu:measurements").as_markup(),
            parse_mode="HTML"
        )
        return
    await cb.answer()

    lines = ["📊 <b>История замеров</b>
"]
    for r in records:
        date = r.recorded_at.strftime("%d.%m") if r.recorded_at else "—"
        w = f"{r.weight_kg}кг" if r.weight_kg else "—"
        lines.append(f"📅 {date}  |  ⚖️ {w}")

    kb = InlineKeyboardBuilder()
    kb.button(text="◀️ Назад", callback_data="menu:measurements")
    await cb.message.edit_text("
".join(lines), reply_markup=kb.as_markup(), parse_mode="HTML")
