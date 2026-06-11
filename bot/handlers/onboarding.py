from datetime import date, datetime
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bot.states.states import CalibrationStates
from bot.keyboards.main_menu import main_menu_keyboard
from models.user import User
from models.profile import Profile, Gender, Goal, ExperienceLevel
from models.user_equipment import UserEquipment
from models.calibration import CalibrationAnswer
from models.exercise import Equipment, EquipmentCategory
from services.calibration import process_calibration

router = Router()


def _kb(*rows):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=d) for t, d in row] for row in rows]
    )

def gender_kb():
    return _kb([("👨 Мужской", "cal:gender:male"), ("👩 Женский", "cal:gender:female")])

def goal_kb():
    return _kb(
        [("💪 Набор массы", "cal:goal:mass_gain")],
        [("⚖️ Поддержка формы", "cal:goal:maintenance")],
        [("🔥 Похудание", "cal:goal:weight_loss")],
        [("🏃 Улучшение кардио", "cal:goal:cardio")],
    )

def experience_kb():
    return _kb(
        [("🆕 Никогда не тренировался", "cal:exp:beginner:0")],
        [("📅 До 6 месяцев", "cal:exp:beginner:4")],
        [("📆 6–24 месяца", "cal:exp:intermediate:12")],
        [("🏆 Больше 2 лет", "cal:exp:advanced:30")],
    )

def health_kb(selected: list[str]):
    flags = [
        ("колени", "knee_injury"), ("поясница", "lower_back_pain"),
        ("плечи", "shoulder_issue"), ("давление", "hypertension"),
        ("грыжа", "hernia"), ("нет ограничений", "none"),
    ]
    rows = []
    for label, code in flags:
        mark = "✅" if code in selected else "➕"
        rows.append([(f"{mark} {label}", f"cal:health:{code}")])
    rows.append([("➡️ Далее", "cal:health:done")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def days_kb():
    return _kb(
        [("2 дня", "cal:days:2"), ("3 дня", "cal:days:3")],
        [("4 дня", "cal:days:4"), ("5 дней", "cal:days:5")],
        [("6 дней", "cal:days:6")],
    )

def duration_kb():
    return _kb(
        [("20 мин", "cal:dur:20"), ("30 мин", "cal:dur:30")],
        [("45 мин", "cal:dur:45"), ("60 мин", "cal:dur:60")],
        [("90 мин", "cal:dur:90")],
    )

async def build_equipment_kb(session: AsyncSession, selected_ids: list[int]) -> InlineKeyboardMarkup:
    result = await session.execute(select(Equipment).order_by(Equipment.category, Equipment.id))
    all_eq = result.scalars().all()
    rows = []
    cat_labels = {
        EquipmentCategory.none: "── 🤸 Без инвентаря ──",
        EquipmentCategory.portable: "── 🎽 Переносной ──",
        EquipmentCategory.stationary: "── 🏗 Тренажёры ──",
    }
    current_cat = None
    for eq in all_eq:
        if eq.category != current_cat:
            current_cat = eq.category
            rows.append([InlineKeyboardButton(text=cat_labels[eq.category], callback_data="cal:eq:noop")])
        mark = "✅" if eq.id in selected_ids else "➕"
        rows.append([InlineKeyboardButton(text=f"{eq.icon or ''} {mark} {eq.name_ru}", callback_data=f"cal:eq:{eq.id}")])
    rows.append([InlineKeyboardButton(text="➡️ Готово", callback_data="cal:eq:done")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ── /start ──────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, user: User, session: AsyncSession):
    result = await session.execute(select(Profile).where(Profile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if profile and profile.calibrated_at:
        await message.answer(
            f"👋 С возвращением, {message.from_user.first_name}!\n\n"
            "Выбери действие:",
            reply_markup=main_menu_keyboard()
        )
        return
    await state.set_state(CalibrationStates.welcome)
    await message.answer(
        f"👋 <b>Привет, {message.from_user.first_name}!</b>\n\n"
        "Я — твой <b>персональный AI-тренер</b>. Я:\n"
        "• Создам тренировки строго под твой инвентарь\n"
        "• Буду вести упражнение за упражнением с фото\n"
        "• Слежу за прогрессом и поднимаю нагрузку сам\n"
        "• Мотивирую уровнями, XP и достижениями\n\n"
        "Пройдём быструю калибровку — займёт ~2 минуты 🚀",
        reply_markup=_kb([("🚀 Поехали!", "cal:start")]),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "cal:start")
async def step_gender(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CalibrationStates.gender)
    await callback.message.edit_text(
        "👤 <b>Шаг 1 / 11 — Пол</b>",
        reply_markup=gender_kb(), parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("cal:gender:"))
async def step_age(callback: CallbackQuery, state: FSMContext):
    await state.update_data(gender=callback.data.split(":")[2])
    await state.set_state(CalibrationStates.age)
    await callback.message.edit_text(
        "🎂 <b>Шаг 2 / 11 — Возраст</b>\n\nНапиши сколько лет (например <code>28</code>):",
        parse_mode="HTML"
    )


@router.message(CalibrationStates.age)
async def step_height(message: Message, state: FSMContext):
    try:
        age = int(message.text.strip())
        assert 10 <= age <= 100
    except Exception:
        await message.answer("Введи корректный возраст (10–100):"); return
    await state.update_data(age=age)
    await state.set_state(CalibrationStates.height)
    await message.answer("📏 <b>Шаг 3 / 11 — Рост</b>\n\nВ сантиметрах (например <code>178</code>):", parse_mode="HTML")


@router.message(CalibrationStates.height)
async def step_weight_current(message: Message, state: FSMContext):
    try:
        h = int(message.text.strip())
        assert 100 <= h <= 250
    except Exception:
        await message.answer("Введи рост в см (100–250):"); return
    await state.update_data(height_cm=h)
    await state.set_state(CalibrationStates.weight_current)
    await message.answer("⚖️ <b>Шаг 4 / 11 — Текущий вес</b>\n\nВ кг (например <code>75.5</code>):", parse_mode="HTML")


@router.message(CalibrationStates.weight_current)
async def step_weight_target(message: Message, state: FSMContext):
    try:
        w = float(message.text.replace(",", ".").strip())
        assert 30 <= w <= 300
    except Exception:
        await message.answer("Введи вес в кг (например 75.5):"); return
    await state.update_data(current_weight_kg=w)
    await state.set_state(CalibrationStates.weight_target)
    await message.answer("🎯 <b>Шаг 5 / 11 — Целевой вес</b>\n\nВ кг:", parse_mode="HTML")


@router.message(CalibrationStates.weight_target)
async def step_goal(message: Message, state: FSMContext):
    try:
        w = float(message.text.replace(",", ".").strip())
        assert 30 <= w <= 300
    except Exception:
        await message.answer("Введи целевой вес в кг:"); return
    await state.update_data(target_weight_kg=w)
    await state.set_state(CalibrationStates.goal)
    await message.answer("🏁 <b>Шаг 6 / 11 — Цель</b>\n\nВыбери главную цель:", reply_markup=goal_kb(), parse_mode="HTML")


@router.callback_query(F.data.startswith("cal:goal:"))
async def step_experience(callback: CallbackQuery, state: FSMContext):
    await state.update_data(goal=callback.data.split(":")[2])
    await state.set_state(CalibrationStates.experience)
    await callback.message.edit_text("💪 <b>Шаг 7 / 11 — Опыт</b>", reply_markup=experience_kb(), parse_mode="HTML")


@router.callback_query(F.data.startswith("cal:exp:"))
async def step_health_flags(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    await state.update_data(experience_level=parts[2], experience_months=int(parts[3]), health_flags=[])
    await state.set_state(CalibrationStates.health_flags)
    await callback.message.edit_text(
        "🏥 <b>Шаг 8 / 11 — Здоровье</b>\n\nОтметь всё что актуально:",
        reply_markup=health_kb([]), parse_mode="HTML"
    )


@router.callback_query(CalibrationStates.health_flags, F.data.startswith("cal:health:"))
async def toggle_health(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    flag = callback.data.split(":")[2]
    if flag == "done":
        await state.update_data(equipment_ids=[])
        await state.set_state(CalibrationStates.equipment)
        await callback.message.edit_text(
            "🎒 <b>Шаг 9 / 11 — Инвентарь</b>\n\nОтметь что у тебя есть:",
            reply_markup=await build_equipment_kb(session, []),
            parse_mode="HTML"
        )
        return
    data = await state.get_data()
    flags = data.get("health_flags", [])
    if flag == "none":
        flags = ["none"]
    else:
        flags = [f for f in flags if f != "none"]
        if flag in flags: flags.remove(flag)
        else: flags.append(flag)
    await state.update_data(health_flags=flags)
    await callback.message.edit_reply_markup(reply_markup=health_kb(flags))
    await callback.answer()


@router.callback_query(CalibrationStates.equipment, F.data.startswith("cal:eq:"))
async def toggle_equipment(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    code = callback.data.split(":")[2]
    if code == "noop":
        await callback.answer(); return
    if code == "done":
        await state.set_state(CalibrationStates.training_days)
        await callback.message.edit_text(
            "📅 <b>Шаг 10 / 11 — Частота</b>\n\nСколько тренировок в неделю?",
            reply_markup=days_kb(), parse_mode="HTML"
        )
        return
    data = await state.get_data()
    eq_ids = data.get("equipment_ids", [])
    eq_id = int(code)
    if eq_id in eq_ids: eq_ids.remove(eq_id)
    else: eq_ids.append(eq_id)
    await state.update_data(equipment_ids=eq_ids)
    await callback.message.edit_reply_markup(reply_markup=await build_equipment_kb(session, eq_ids))
    await callback.answer()


@router.callback_query(F.data.startswith("cal:days:"))
async def step_duration(callback: CallbackQuery, state: FSMContext):
    await state.update_data(days_per_week=int(callback.data.split(":")[2]))
    await state.set_state(CalibrationStates.duration)
    await callback.message.edit_text(
        "⏱ <b>Шаг 11 / 11 — Длительность</b>\n\nЖелаемое время одной тренировки:",
        reply_markup=duration_kb(), parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("cal:dur:"))
async def finish_calibration(callback: CallbackQuery, state: FSMContext, user: User, session: AsyncSession):
    duration = int(callback.data.split(":")[2])
    await state.update_data(preferred_duration_min=duration)
    data = await state.get_data()
    await state.clear()

    # ── Run calibration service ──
    cal = process_calibration(
        experience_level=ExperienceLevel(data["experience_level"]),
        experience_months=data["experience_months"],
        age=data.get("age", 25),
        health_flags=data.get("health_flags", []),
        days_per_week=data["days_per_week"],
        preferred_duration_min=duration,
        goal=Goal(data["goal"]),
    )

    # ── Upsert profile ──
    birth_year = datetime.now().year - data.get("age", 25)
    existing = await session.execute(select(Profile).where(Profile.user_id == user.id))
    profile = existing.scalar_one_or_none()
    pdata = dict(
        gender=Gender(data["gender"]),
        birth_date=date(birth_year, 6, 1),
        height_cm=data["height_cm"],
        current_weight_kg=data["current_weight_kg"],
        target_weight_kg=data["target_weight_kg"],
        goal=Goal(data["goal"]),
        experience_level=ExperienceLevel(data["experience_level"]),
        training_experience_months=data["experience_months"],
        training_structure=cal.training_structure,
        split_type=cal.split_type,
        intensity_level=cal.intensity_level,
        preferred_duration_min=duration,
        health_flags=data.get("health_flags", []),
        calibrated_at=datetime.utcnow(),
    )
    if not profile:
        profile = Profile(user_id=user.id, **pdata)
        session.add(profile)
    else:
        for k, v in pdata.items():
            setattr(profile, k, v)

    # ── Save equipment ──
    eq_ids = data.get("equipment_ids", [])
    bw_result = await session.execute(select(Equipment).where(Equipment.category == EquipmentCategory.none).limit(1))
    bw = bw_result.scalar_one_or_none()
    if bw and bw.id not in eq_ids:
        eq_ids.append(bw.id)

    for eq_id in eq_ids:
        exists = await session.execute(select(UserEquipment).where(
            UserEquipment.user_id == user.id, UserEquipment.equipment_id == eq_id
        ))
        if not exists.scalar_one_or_none():
            session.add(UserEquipment(user_id=user.id, equipment_id=eq_id))

    # ── Save calibration log ──
    session.add(CalibrationAnswer(user_id=user.id, question_key="full_calibration", answer=data))
    await session.commit()

    # ── Build summary ──
    goals_ru = {"mass_gain": "💪 Набор массы", "maintenance": "⚖️ Поддержка", "weight_loss": "🔥 Похудание", "cardio": "🏃 Кардио"}
    struct_label = "Всё тело (Fullbody)" if cal.training_structure.value == "fullbody" else f"Сплит — {cal.split_type.value if cal.split_type else ''}"
    intensity_bar = "🟩" * cal.intensity_level + "⬜" * (5 - cal.intensity_level)

    await callback.message.edit_text(
        "✅ <b>Калибровка завершена!</b>\n\n"
        "Твой профиль тренировок:\n\n"
        f"🎯 <b>Цель:</b> {goals_ru.get(data['goal'], data['goal'])}\n"
        f"📊 <b>Структура:</b> {struct_label}\n"
        f"⚡ <b>Интенсивность:</b> {intensity_bar} ({cal.intensity_level}/5)\n"
        f"📅 <b>Дней в нед.:</b> {cal.recommended_days_per_week}\n"
        f"⏱ <b>Длительность:</b> {cal.recommended_duration_min} мин\n\n"
        "Готов к первой тренировке? 💪",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
