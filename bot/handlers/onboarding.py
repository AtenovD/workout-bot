from datetime import date, datetime
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bot.states.states import OnboardingStates
from bot.keyboards.main_menu import main_menu_keyboard
from models.user import User
from models.profile import Profile, Gender, Goal, ExperienceLevel
from models.user_equipment import UserEquipment
from models.calibration import CalibrationAnswer
from models.exercise import Exercise, Equipment, EquipmentCategory
from services.calibration import process_calibration
from bot.utils.message_edit import safe_edit_text

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
        [("🔄 Был опыт, сейчас возвращаюсь", "cal:exp:intermediate:0")],
    )

def health_kb(selected: list[str]):
    flags = [
        ("Колени: боль, травмы, нестабильность", "knee_injury"),
        ("Колени: иногда болят, но без диагноза", "knee_pain"),
        ("Поясница: боль, протрузии, дискомфорт", "lower_back_pain"),
        ("Грыжа/протрузия диска позвоночника", "spinal_disc_hernia"),
        ("Плечи: боль, импинджмент, ограничение движения", "shoulder_issue"),
        ("Давление / сердце: осторожнее с пульсом и отказом", "hypertension"),
        ("Сердце: диагноз или запрет на тяжёлые нагрузки", "heart_condition"),
        ("Грыжа пищевода / хиатальная", "hiatal_hernia"),
        ("Паховая грыжа", "inguinal_hernia"),
        ("Пупочная / брюшная грыжа", "umbilical_hernia"),
        ("Другая грыжа / не уверен", "hernia"),
        ("Нет ограничений", "none"),
    ]
    rows = []
    for label, code in flags:
        mark = "✅" if code in selected else "➕"
        rows.append([InlineKeyboardButton(text=f"{mark} {label}", callback_data=f"cal:health:{code}")])
    rows.append([InlineKeyboardButton(text="➡️ Далее", callback_data="cal:health:done")])
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

CATEGORY_META_ONBOARDING = {
    EquipmentCategory.none:       {"label_ru": "🤸 Без инвентаря", "desc_ru": "Упражнения с собственным весом"},
    EquipmentCategory.portable:   {"label_ru": "🎽 Переносной инвентарь", "desc_ru": "Гантели, гири, резинки, скакалка…"},
    EquipmentCategory.stationary: {"label_ru": "🏗 Стационарный инвентарь", "desc_ru": "Штанги, тренажёры, скамьи, турник…"},
}


async def build_category_kb() -> InlineKeyboardMarkup:
    rows = []
    for cat in (EquipmentCategory.none, EquipmentCategory.portable, EquipmentCategory.stationary):
        meta = CATEGORY_META_ONBOARDING[cat]
        rows.append([InlineKeyboardButton(text=meta["label_ru"], callback_data=f"eq_cat:{cat.value}")])
    rows.append([InlineKeyboardButton(text="➡️ Готово", callback_data="eq_done")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def build_equipment_items_kb(session: AsyncSession, selected_ids: list[int], category: str) -> InlineKeyboardMarkup:
    active_result = await session.execute(
        select(Exercise.required_equipment_id)
        .where(Exercise.is_active == True, Exercise.required_equipment_id.is_not(None))
        .distinct()
    )
    active_equipment_ids = {row[0] for row in active_result.fetchall() if row[0]}
    result = await session.execute(
        select(Equipment).where(Equipment.category == category).order_by(Equipment.id)
    )
    items = []
    seen_labels: set[str] = set()
    for eq in result.scalars().all():
        if eq.category != EquipmentCategory.none and eq.id not in active_equipment_ids:
            continue
        label_key = (eq.name_ru or eq.name_en or eq.code).strip().lower()
        if label_key in seen_labels:
            continue
        seen_labels.add(label_key)
        items.append(eq)
    rows = []
    for eq in items:
        mark = "✅" if eq.id in selected_ids else "⬜"
        rows.append([InlineKeyboardButton(
            text=f"{mark} {eq.name_ru}{(' ' + eq.icon) if eq.icon else ''}",
            callback_data=f"eq_tgl:{eq.id}:{category}",
        )])
    rows.append([InlineKeyboardButton(text="🔙 Назад к категориям", callback_data="eq_back_cat")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, user: User, session: AsyncSession):
    result = await session.execute(select(Profile).where(Profile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if profile and profile.calibrated_at:
        await message.answer(
            f"⚡ <b>GYM Control Center</b>\n\n"
            f"С возвращением, <b>{message.from_user.first_name}</b>.\n"
            "Твоя тренировочная система готова: можно начать занятие, проверить прогресс, "
            "открыть достижения, настроить расписание или обновить инвентарь.\n\n"
            "Выбери модуль ниже — я подстрою следующий шаг под твой профиль.",
            reply_markup=main_menu_keyboard(lang=user.language_code or "ru"),
            parse_mode="HTML",
        )
        return

    await state.set_state(OnboardingStates.language)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="onboarding_lang:ru"),
         InlineKeyboardButton(text="🇬🇧 English", callback_data="onboarding_lang:en")]
    ])
    await message.answer("🌍 Выбери язык / Choose language:", reply_markup=kb)
    return


@router.callback_query(F.data.startswith("onboarding_lang:"))
async def onboarding_language(callback: CallbackQuery, state: FSMContext, user: User, session: AsyncSession):
    lang = callback.data.split(":")[1]
    if lang not in {"ru", "en"}:
        await callback.answer("Unsupported language", show_alert=True)
        return
    user.language_code = lang
    await session.commit()
    await state.update_data(language=lang)
    await state.set_state(OnboardingStates.welcome)
    if lang == "en":
        text = (
            f"👋 <b>Hi, {callback.from_user.first_name}!</b>\n\n"
            "I am your <b>personal AI coach</b>. I will:\n"
            "• Build workouts strictly around your inventory\n"
            "• Guide you exercise by exercise with visuals\n"
            "• Track progress and adjust load automatically\n"
            "• Motivate you with XP, levels, and achievements\n\n"
            "Let's run a quick calibration — about 2 minutes 🚀"
        )
        button = "🚀 Let's go!"
    else:
        text = (
            f"👋 <b>Привет, {callback.from_user.first_name}!</b>\n\n"
            "Я — твой <b>персональный AI-тренер</b>. Я:\n"
            "• Создам тренировки строго под твой инвентарь\n"
            "• Буду вести упражнение за упражнением с фото\n"
            "• Слежу за прогрессом и поднимаю нагрузку сам\n"
            "• Мотивирую уровнями, XP и достижениями\n\n"
            "Пройдём быструю калибровку — займёт ~2 минуты 🚀"
        )
    await safe_edit_text(callback.message,
        text,
        reply_markup=_kb([(button if lang == "en" else "🚀 Поехали!", "cal:start")]),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "cal:start")
async def step_gender(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OnboardingStates.gender)
    await safe_edit_text(callback.message,
        "👤 <b>Шаг 1 / 11 — Пол</b>",
        reply_markup=gender_kb(), parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("cal:gender:"))
async def step_age(callback: CallbackQuery, state: FSMContext):
    await state.update_data(gender=callback.data.split(":")[2])
    await state.set_state(OnboardingStates.age)
    await safe_edit_text(callback.message,
        "🎂 <b>Шаг 2 / 11 — Возраст</b>\n\nНапиши сколько лет (например <code>28</code>):",
        parse_mode="HTML"
    )


@router.message(OnboardingStates.age, F.text)
async def step_height(message: Message, state: FSMContext):
    try:
        age = int(message.text.strip())
        assert 10 <= age <= 100
    except Exception:
        await message.answer("Введи корректный возраст (10–100):"); return
    await state.update_data(age=age)
    await state.set_state(OnboardingStates.height)
    await message.answer("📏 <b>Шаг 3 / 11 — Рост</b>\n\nВ сантиметрах (например <code>178</code>):", parse_mode="HTML")


@router.message(OnboardingStates.height, F.text)
async def step_weight_current(message: Message, state: FSMContext):
    try:
        h = int(message.text.strip())
        assert 100 <= h <= 250
    except Exception:
        await message.answer("Введи рост в см (100–250):"); return
    await state.update_data(height_cm=h)
    await state.set_state(OnboardingStates.weight_current)
    await message.answer("⚖️ <b>Шаг 4 / 11 — Текущий вес</b>\n\nВ кг (например <code>75.5</code>):", parse_mode="HTML")


@router.message(OnboardingStates.weight_current, F.text)
async def step_weight_target(message: Message, state: FSMContext):
    try:
        w = float(message.text.replace(",", ".").strip())
        assert 30 <= w <= 300
    except Exception:
        await message.answer("Введи вес в кг (например 75.5):"); return
    await state.update_data(current_weight_kg=w)
    await state.set_state(OnboardingStates.weight_target)
    await message.answer("🎯 <b>Шаг 5 / 11 — Целевой вес</b>\n\nВ кг:", parse_mode="HTML")


@router.message(OnboardingStates.weight_target, F.text)
async def step_goal(message: Message, state: FSMContext):
    try:
        w = float(message.text.replace(",", ".").strip())
        assert 30 <= w <= 300
    except Exception:
        await message.answer("Введи целевой вес в кг:"); return
    await state.update_data(target_weight_kg=w)
    await state.set_state(OnboardingStates.goal)
    await message.answer("🏁 <b>Шаг 6 / 11 — Цель</b>\n\nВыбери главную цель:", reply_markup=goal_kb(), parse_mode="HTML")


@router.callback_query(F.data.startswith("cal:goal:"))
async def step_experience(callback: CallbackQuery, state: FSMContext):
    await state.update_data(goal=callback.data.split(":")[2])
    await state.set_state(OnboardingStates.experience)
    await safe_edit_text(callback.message, "💪 <b>Шаг 7 / 11 — Опыт</b>", reply_markup=experience_kb(), parse_mode="HTML")


@router.callback_query(OnboardingStates.experience, F.data.startswith("cal:exp:"))
async def step_health_flags(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    await state.update_data(experience_level=parts[2], experience_months=int(parts[3]), health_flags=[])
    await state.set_state(OnboardingStates.health_flags)
    await safe_edit_text(callback.message,
        "🏥 <b>Шаг 8 / 11 — Здоровье и ограничения</b>\n\n"
        "Отметь всё, что может влиять на подбор упражнений. Это не диагноз и не замена врачу, "
        "но бот будет осторожнее с осевой нагрузкой, давлением внутри живота, отказными подходами "
        "и упражнениями, которые могут раздражать проблемную зону.",
        reply_markup=health_kb([]), parse_mode="HTML"
    )


@router.callback_query(OnboardingStates.health_flags, F.data.startswith("cal:health:"))
async def toggle_health(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    flag = callback.data.split(":")[2]
    if flag == "done":
        await state.update_data(equipment_ids=[])
        await state.set_state(OnboardingStates.equipment)
        await safe_edit_text(callback.message,
            "🎒 <b>Шаг 9 / 11 — Инвентарь</b>\n\nОтметь что у тебя есть:",
            reply_markup=await build_category_kb(),
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



# ── Onboarding: step 1 (pick category) ──
@router.callback_query(OnboardingStates.equipment, F.data.startswith("eq_cat:"))
async def eq_pick_category_onboarding(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    category = call.data.split(":", 1)[1]
    data = await state.get_data()
    selected = list(data.get("equipment_ids", []))
    meta = CATEGORY_META_ONBOARDING.get(EquipmentCategory(category), CATEGORY_META_ONBOARDING[EquipmentCategory.none])
    await state.update_data(current_eq_category=category)
    await safe_edit_text(call.message,
        f"{meta['label_ru']}\n{meta['desc_ru']}\n\n"
        "<i>Нажми на предмет, чтобы добавить/убрать его.</i>",
        reply_markup=await build_equipment_items_kb(session, selected, category),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(OnboardingStates.equipment, F.data == "eq_back_cat")
async def eq_back_to_categories_onboarding(call: CallbackQuery, state: FSMContext):
    await state.update_data(current_eq_category=None)
    await safe_edit_text(call.message,
        "🏋️ <b>Выбери доступный инвентарь</b>:",
        reply_markup=await build_category_kb(),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(OnboardingStates.equipment, F.data.startswith("eq_tgl:"))
async def toggle_equipment_onboarding(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    _, eq_id_str, category = call.data.split(":", 2)
    if eq_id_str.isdigit():
        eq_id = int(eq_id_str)
    else:
        eq = (await session.execute(select(Equipment).where(Equipment.code == eq_id_str))).scalar_one_or_none()
        if not eq:
            await call.answer("Инвентарь не найден.", show_alert=True)
            return
        eq_id = eq.id
        category = eq.category.value if hasattr(eq.category, "value") else str(eq.category)
    data = await state.get_data()
    selected = list(data.get("equipment_ids", []))
    if eq_id in selected:
        selected.remove(eq_id)
    else:
        selected.append(eq_id)
    await state.update_data(equipment_ids=selected)
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Equipment toggle: user={call.from_user.id}, eq_id={eq_id}, total_selected={len(selected)}")
    await call.message.edit_reply_markup(
        reply_markup=await build_equipment_items_kb(session, selected, category)
    )
    await call.answer()


@router.callback_query(OnboardingStates.equipment, F.data == "eq_done")
async def finish_equipment_onboarding(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_count = len(data.get("equipment_ids", []))
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Equipment done: user={call.from_user.id}, selected={selected_count} items")
    await state.set_state(OnboardingStates.training_days)
    await safe_edit_text(call.message,
        "📅 <b>Шаг 10 / 11 — Дни в неделю</b>\n\nСколько дней в неделю хочешь тренироваться?",
        reply_markup=days_kb(), parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(OnboardingStates.training_days, F.data.startswith("cal:days:"))
async def step_duration(callback: CallbackQuery, state: FSMContext):
    await state.update_data(days_per_week=int(callback.data.split(":")[2]))
    await state.set_state(OnboardingStates.duration)
    await safe_edit_text(callback.message,
        "⏱ <b>Шаг 11 / 11 — Длительность</b>\n\nЖелаемое время одной тренировки:",
        reply_markup=duration_kb(), parse_mode="HTML"
    )


@router.callback_query(OnboardingStates.duration, F.data.startswith("cal:dur:"))
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

    await safe_edit_text(callback.message,
        "✅ <b>Калибровка завершена!</b>\n\n"
        "Твой профиль тренировок:\n\n"
        f"🎯 <b>Цель:</b> {goals_ru.get(data['goal'], data['goal'])}\n"
        f"📊 <b>Структура:</b> {struct_label}\n"
        f"⚡ <b>Интенсивность:</b> {intensity_bar} ({cal.intensity_level}/5)\n"
        f"📅 <b>Дней в нед.:</b> {cal.recommended_days_per_week}\n"
        f"⏱ <b>Длительность:</b> {cal.recommended_duration_min} мин\n\n"
        "Готов к первой тренировке? 💪",
        reply_markup=main_menu_keyboard(lang=data.get("language", user.language_code or "ru")),
        parse_mode="HTML",
    )
