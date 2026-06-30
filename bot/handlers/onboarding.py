from datetime import date, datetime

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.main_menu import main_menu_keyboard
from bot.states.states import OnboardingStates
from bot.utils.message_edit import safe_edit_text
from models.calibration import CalibrationAnswer
from models.exercise import Equipment, EquipmentCategory, Exercise
from models.profile import ExperienceLevel, Gender, Goal, Profile
from models.user import User
from models.user_equipment import UserEquipment
from services.calibration import process_calibration
from services.strength_calibration import save_strength_calibration, strength_calibration_help

router = Router()


def _lang(value: str | None) -> str:
    return "en" if value == "en" else "ru"


async def _current_lang(state: FSMContext, user: User | None = None) -> str:
    data = await state.get_data()
    return _lang(data.get("language") or (user.language_code if user else None))


def _kb(*rows):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=data) for text, data in row] for row in rows]
    )


def gender_kb(lang: str):
    if lang == "en":
        return _kb([("👨 Male", "cal:gender:male"), ("👩 Female", "cal:gender:female")])
    return _kb([("👨 Мужской", "cal:gender:male"), ("👩 Женский", "cal:gender:female")])


def goal_kb(lang: str):
    if lang == "en":
        return _kb(
            [("💪 Muscle gain", "cal:goal:mass_gain")],
            [("⚖️ Maintenance", "cal:goal:maintenance")],
            [("🔥 Fat loss", "cal:goal:weight_loss")],
            [("🏃 Better cardio", "cal:goal:cardio")],
        )
    return _kb(
        [("💪 Набор массы", "cal:goal:mass_gain")],
        [("⚖️ Поддержка формы", "cal:goal:maintenance")],
        [("🔥 Похудание", "cal:goal:weight_loss")],
        [("🏃 Улучшение кардио", "cal:goal:cardio")],
    )


def experience_kb(lang: str):
    if lang == "en":
        return _kb(
            [("🆕 Never trained", "cal:exp:beginner:0")],
            [("📅 Up to 6 months", "cal:exp:beginner:4")],
            [("📆 6-24 months", "cal:exp:intermediate:12")],
            [("🏆 More than 2 years", "cal:exp:advanced:30")],
            [("🔄 Returning after a break", "cal:exp:intermediate:0")],
        )
    return _kb(
        [("🆕 Никогда не тренировался", "cal:exp:beginner:0")],
        [("📅 До 6 месяцев", "cal:exp:beginner:4")],
        [("📆 6-24 месяца", "cal:exp:intermediate:12")],
        [("🏆 Больше 2 лет", "cal:exp:advanced:30")],
        [("🔄 Был опыт, сейчас возвращаюсь", "cal:exp:intermediate:0")],
    )


HEALTH_FLAGS = {
    "ru": [
        ("Колени: боль, травмы, нестабильность", "knee_injury"),
        ("Колени: иногда болят, но без диагноза", "knee_pain"),
        ("Поясница: боль, протрузии, дискомфорт", "lower_back_pain"),
        ("Грыжа/протрузия диска позвоночника", "spinal_disc_hernia"),
        ("Плечи: боль, импинджмент, ограничение движения", "shoulder_issue"),
        ("Давление / сердце: осторожнее с пульсом и отказом", "hypertension"),
        ("Сердце: диагноз или запрет на тяжелые нагрузки", "heart_condition"),
        ("Грыжа пищевода / хиатальная", "hiatal_hernia"),
        ("Паховая грыжа", "inguinal_hernia"),
        ("Пупочная / брюшная грыжа", "umbilical_hernia"),
        ("Другая грыжа / не уверен", "hernia"),
        ("Нет ограничений", "none"),
    ],
    "en": [
        ("Knees: pain, injury, instability", "knee_injury"),
        ("Knees: occasional pain, no diagnosis", "knee_pain"),
        ("Lower back: pain, disc issues, discomfort", "lower_back_pain"),
        ("Spinal disc hernia / protrusion", "spinal_disc_hernia"),
        ("Shoulders: pain, impingement, limited range", "shoulder_issue"),
        ("Blood pressure / heart: be careful with pulse and failure", "hypertension"),
        ("Heart condition or heavy-load restriction", "heart_condition"),
        ("Hiatal hernia / reflux-sensitive", "hiatal_hernia"),
        ("Inguinal hernia", "inguinal_hernia"),
        ("Umbilical / abdominal hernia", "umbilical_hernia"),
        ("Other hernia / not sure", "hernia"),
        ("No limitations", "none"),
    ],
}


def health_kb(selected: list[str], lang: str):
    rows = []
    for label, code in HEALTH_FLAGS[lang]:
        mark = "✅" if code in selected else "➕"
        rows.append([InlineKeyboardButton(text=f"{mark} {label}", callback_data=f"cal:health:{code}")])
    next_text = "➡️ Next" if lang == "en" else "➡️ Далее"
    rows.append([InlineKeyboardButton(text=next_text, callback_data="cal:health:done")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def days_kb(lang: str):
    day = "days" if lang == "en" else "дня"
    days = "days" if lang == "en" else "дней"
    return _kb(
        [(f"2 {day}", "cal:days:2"), (f"3 {day}", "cal:days:3")],
        [(f"4 {day}", "cal:days:4"), (f"5 {days}", "cal:days:5")],
        [(f"6 {days}", "cal:days:6")],
    )


def duration_kb(lang: str):
    minute = "min" if lang == "en" else "мин"
    return _kb(
        [(f"20 {minute}", "cal:dur:20"), (f"30 {minute}", "cal:dur:30")],
        [(f"45 {minute}", "cal:dur:45"), (f"60 {minute}", "cal:dur:60")],
        [(f"90 {minute}", "cal:dur:90")],
    )


def strength_calibration_kb(lang: str):
    if lang == "en":
        return _kb(
            [("✍️ Enter working weights", "cal:strength:enter")],
            [("⏭ Skip, calibrate in first workout", "cal:strength:skip")],
        )
    return _kb(
        [("✍️ Ввести рабочие веса", "cal:strength:enter")],
        [("⏭ Пропустить, откалибровать на первой тренировке", "cal:strength:skip")],
    )


CATEGORY_META_ONBOARDING = {
    EquipmentCategory.none: {
        "label_ru": "🤸 Без инвентаря",
        "desc_ru": "Упражнения с собственным весом",
        "label_en": "🤸 No equipment",
        "desc_en": "Bodyweight exercises",
    },
    EquipmentCategory.portable: {
        "label_ru": "🎽 Переносной инвентарь",
        "desc_ru": "Гантели, гири, резинки, скакалка...",
        "label_en": "🎽 Portable equipment",
        "desc_en": "Dumbbells, kettlebells, bands, jump rope...",
    },
    EquipmentCategory.stationary: {
        "label_ru": "🏗 Стационарный инвентарь",
        "desc_ru": "Штанги, тренажеры, скамьи, турник...",
        "label_en": "🏗 Stationary equipment",
        "desc_en": "Barbells, machines, benches, pull-up bar...",
    },
}


async def build_category_kb(lang: str) -> InlineKeyboardMarkup:
    rows = []
    label_key = "label_en" if lang == "en" else "label_ru"
    for cat in (EquipmentCategory.none, EquipmentCategory.portable, EquipmentCategory.stationary):
        rows.append([InlineKeyboardButton(text=CATEGORY_META_ONBOARDING[cat][label_key], callback_data=f"eq_cat:{cat.value}")])
    rows.append([InlineKeyboardButton(text="➡️ Done" if lang == "en" else "➡️ Готово", callback_data="eq_done")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def build_equipment_items_kb(
    session: AsyncSession,
    selected_ids: list[int],
    category: str,
    lang: str,
) -> InlineKeyboardMarkup:
    active_result = await session.execute(
        select(Exercise.required_equipment_id)
        .where(Exercise.is_active == True, Exercise.required_equipment_id.is_not(None))
        .distinct()
    )
    active_equipment_ids = {row[0] for row in active_result.fetchall() if row[0]}
    result = await session.execute(select(Equipment).where(Equipment.category == category).order_by(Equipment.id))
    items = []
    seen_labels: set[str] = set()
    for eq in result.scalars().all():
        if eq.category != EquipmentCategory.none and eq.id not in active_equipment_ids:
            continue
        label = (eq.name_en if lang == "en" else eq.name_ru) or eq.name_en or eq.name_ru or eq.code
        label_key = label.strip().lower()
        if label_key in seen_labels:
            continue
        seen_labels.add(label_key)
        items.append((eq, label))

    rows = []
    for eq, label in items:
        mark = "✅" if eq.id in selected_ids else "⬜"
        icon = f" {eq.icon}" if eq.icon else ""
        rows.append([InlineKeyboardButton(text=f"{mark} {label}{icon}", callback_data=f"eq_tgl:{eq.id}:{category}")])
    back = "🔙 Back to categories" if lang == "en" else "🔙 Назад к категориям"
    rows.append([InlineKeyboardButton(text=back, callback_data="eq_back_cat")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _welcome_back_text(first_name: str, lang: str) -> str:
    if lang == "en":
        return (
            f"⚡ <b>GYM Control Center</b>\n\n"
            f"Welcome back, <b>{first_name}</b>.\n"
            "Your training system is ready: start a workout, check progress, open achievements, adjust schedule, or update inventory.\n\n"
            "Choose a module below and I will open the next screen for your profile."
        )
    return (
        f"⚡ <b>GYM Control Center</b>\n\n"
        f"С возвращением, <b>{first_name}</b>.\n"
        "Твоя тренировочная система готова: можно начать занятие, проверить прогресс, открыть достижения, настроить расписание или обновить инвентарь.\n\n"
        "Выбери модуль ниже — я подстрою следующий шаг под твой профиль."
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, user: User, session: AsyncSession):
    result = await session.execute(select(Profile).where(Profile.user_id == user.id))
    profile = result.scalar_one_or_none()
    lang = _lang(user.language_code)
    if profile and profile.calibrated_at:
        await message.answer(
            _welcome_back_text(message.from_user.first_name, lang),
            reply_markup=main_menu_keyboard(lang=lang, telegram_id=user.telegram_id),
            parse_mode="HTML",
        )
        return

    await state.set_state(OnboardingStates.language)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="onboarding_lang:ru"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="onboarding_lang:en"),
            ]
        ]
    )
    await message.answer("🌍 Выбери язык / Choose language:", reply_markup=kb)


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
            "• Прослежу за прогрессом и сам подниму нагрузку\n"
            "• Добавлю мотивацию через уровни, XP и достижения\n\n"
            "Пройдем быструю калибровку — займет ~2 минуты 🚀"
        )
        button = "🚀 Поехали!"
    await safe_edit_text(callback.message, text, reply_markup=_kb([(button, "cal:start")]), parse_mode="HTML")


@router.callback_query(F.data == "cal:start")
async def step_gender(callback: CallbackQuery, state: FSMContext, user: User):
    lang = await _current_lang(state, user)
    await state.set_state(OnboardingStates.gender)
    text = "👤 <b>Step 1 / 11 — Gender</b>" if lang == "en" else "👤 <b>Шаг 1 / 11 — Пол</b>"
    await safe_edit_text(callback.message, text, reply_markup=gender_kb(lang), parse_mode="HTML")


@router.callback_query(F.data.startswith("cal:gender:"))
async def step_age(callback: CallbackQuery, state: FSMContext, user: User):
    lang = await _current_lang(state, user)
    await state.update_data(gender=callback.data.split(":")[2])
    await state.set_state(OnboardingStates.age)
    text = (
        "🎂 <b>Step 2 / 11 — Age</b>\n\nEnter your age, for example <code>28</code>:"
        if lang == "en"
        else "🎂 <b>Шаг 2 / 11 — Возраст</b>\n\nНапиши сколько лет, например <code>28</code>:"
    )
    await safe_edit_text(callback.message, text, parse_mode="HTML")


@router.message(OnboardingStates.age, F.text)
async def step_height(message: Message, state: FSMContext, user: User):
    lang = await _current_lang(state, user)
    try:
        age = int(message.text.strip())
        assert 10 <= age <= 100
    except Exception:
        await message.answer("Enter a valid age (10-100):" if lang == "en" else "Введи корректный возраст (10-100):")
        return
    await state.update_data(age=age)
    await state.set_state(OnboardingStates.height)
    text = (
        "📏 <b>Step 3 / 11 — Height</b>\n\nIn centimeters, for example <code>178</code>:"
        if lang == "en"
        else "📏 <b>Шаг 3 / 11 — Рост</b>\n\nВ сантиметрах, например <code>178</code>:"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(OnboardingStates.height, F.text)
async def step_weight_current(message: Message, state: FSMContext, user: User):
    lang = await _current_lang(state, user)
    try:
        height = int(message.text.strip())
        assert 100 <= height <= 250
    except Exception:
        await message.answer("Enter height in cm (100-250):" if lang == "en" else "Введи рост в см (100-250):")
        return
    await state.update_data(height_cm=height)
    await state.set_state(OnboardingStates.weight_current)
    text = (
        "⚖️ <b>Step 4 / 11 — Current weight</b>\n\nIn kg, for example <code>75.5</code>:"
        if lang == "en"
        else "⚖️ <b>Шаг 4 / 11 — Текущий вес</b>\n\nВ кг, например <code>75.5</code>:"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(OnboardingStates.weight_current, F.text)
async def step_weight_target(message: Message, state: FSMContext, user: User):
    lang = await _current_lang(state, user)
    try:
        weight = float(message.text.replace(",", ".").strip())
        assert 30 <= weight <= 300
    except Exception:
        await message.answer("Enter weight in kg, for example 75.5:" if lang == "en" else "Введи вес в кг, например 75.5:")
        return
    await state.update_data(current_weight_kg=weight)
    await state.set_state(OnboardingStates.weight_target)
    text = (
        "🎯 <b>Step 5 / 11 — Target weight</b>\n\nIn kg:"
        if lang == "en"
        else "🎯 <b>Шаг 5 / 11 — Целевой вес</b>\n\nВ кг:"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(OnboardingStates.weight_target, F.text)
async def step_goal(message: Message, state: FSMContext, user: User):
    lang = await _current_lang(state, user)
    try:
        weight = float(message.text.replace(",", ".").strip())
        assert 30 <= weight <= 300
    except Exception:
        await message.answer("Enter target weight in kg:" if lang == "en" else "Введи целевой вес в кг:")
        return
    await state.update_data(target_weight_kg=weight)
    await state.set_state(OnboardingStates.goal)
    text = (
        "🏁 <b>Step 6 / 11 — Goal</b>\n\nChoose your main goal:"
        if lang == "en"
        else "🏁 <b>Шаг 6 / 11 — Цель</b>\n\nВыбери главную цель:"
    )
    await message.answer(text, reply_markup=goal_kb(lang), parse_mode="HTML")


@router.callback_query(F.data.startswith("cal:goal:"))
async def step_experience(callback: CallbackQuery, state: FSMContext, user: User):
    lang = await _current_lang(state, user)
    await state.update_data(goal=callback.data.split(":")[2])
    await state.set_state(OnboardingStates.experience)
    text = "💪 <b>Step 7 / 11 — Experience</b>" if lang == "en" else "💪 <b>Шаг 7 / 11 — Опыт</b>"
    await safe_edit_text(callback.message, text, reply_markup=experience_kb(lang), parse_mode="HTML")


@router.callback_query(OnboardingStates.experience, F.data.startswith("cal:exp:"))
async def step_health_flags(callback: CallbackQuery, state: FSMContext, user: User):
    lang = await _current_lang(state, user)
    parts = callback.data.split(":")
    await state.update_data(experience_level=parts[2], experience_months=int(parts[3]), health_flags=[])
    await state.set_state(OnboardingStates.health_flags)
    if lang == "en":
        text = (
            "🏥 <b>Step 8 / 11 — Health and limitations</b>\n\n"
            "Mark everything that can affect exercise selection. This is not a diagnosis or a replacement for a doctor, "
            "but the bot will be more careful with axial load, intra-abdominal pressure, failure sets, and movements that can irritate problem areas."
        )
    else:
        text = (
            "🏥 <b>Шаг 8 / 11 — Здоровье и ограничения</b>\n\n"
            "Отметь все, что может влиять на подбор упражнений. Это не диагноз и не замена врача, "
            "но бот будет осторожнее с осевой нагрузкой, давлением внутри живота, отказными подходами и движениями для проблемных зон."
        )
    await safe_edit_text(callback.message, text, reply_markup=health_kb([], lang), parse_mode="HTML")


@router.callback_query(OnboardingStates.health_flags, F.data.startswith("cal:health:"))
async def toggle_health(callback: CallbackQuery, state: FSMContext, session: AsyncSession, user: User):
    lang = await _current_lang(state, user)
    flag = callback.data.split(":")[2]
    if flag == "done":
        await state.update_data(equipment_ids=[])
        await state.set_state(OnboardingStates.equipment)
        text = (
            "🎒 <b>Step 9 / 11 — Equipment</b>\n\nMark what you have:"
            if lang == "en"
            else "🎒 <b>Шаг 9 / 11 — Инвентарь</b>\n\nОтметь что у тебя есть:"
        )
        await safe_edit_text(callback.message, text, reply_markup=await build_category_kb(lang), parse_mode="HTML")
        return

    data = await state.get_data()
    flags = data.get("health_flags", [])
    if flag == "none":
        flags = ["none"]
    else:
        flags = [item for item in flags if item != "none"]
        if flag in flags:
            flags.remove(flag)
        else:
            flags.append(flag)
    await state.update_data(health_flags=flags)
    await callback.message.edit_reply_markup(reply_markup=health_kb(flags, lang))
    await callback.answer()


@router.callback_query(OnboardingStates.equipment, F.data.startswith("eq_cat:"))
async def eq_pick_category_onboarding(call: CallbackQuery, state: FSMContext, session: AsyncSession, user: User):
    lang = await _current_lang(state, user)
    category = call.data.split(":", 1)[1]
    data = await state.get_data()
    selected = list(data.get("equipment_ids", []))
    meta = CATEGORY_META_ONBOARDING.get(EquipmentCategory(category), CATEGORY_META_ONBOARDING[EquipmentCategory.none])
    label = meta["label_en"] if lang == "en" else meta["label_ru"]
    desc = meta["desc_en"] if lang == "en" else meta["desc_ru"]
    hint = (
        "<i>Tap an item to add/remove it from your inventory.</i>"
        if lang == "en"
        else "<i>Нажми на предмет, чтобы добавить/убрать его из своего инвентаря.</i>"
    )
    await state.update_data(current_eq_category=category)
    await safe_edit_text(
        call.message,
        f"{label}\n{desc}\n\n{hint}",
        reply_markup=await build_equipment_items_kb(session, selected, category, lang),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(OnboardingStates.equipment, F.data == "eq_back_cat")
async def eq_back_to_categories_onboarding(call: CallbackQuery, state: FSMContext, user: User):
    lang = await _current_lang(state, user)
    await state.update_data(current_eq_category=None)
    text = (
        "🏋️ <b>Choose available equipment</b>:"
        if lang == "en"
        else "🏋️ <b>Выбери доступный инвентарь</b>:"
    )
    await safe_edit_text(call.message, text, reply_markup=await build_category_kb(lang), parse_mode="HTML")
    await call.answer()


@router.callback_query(OnboardingStates.equipment, F.data.startswith("eq_tgl:"))
async def toggle_equipment_onboarding(call: CallbackQuery, state: FSMContext, session: AsyncSession, user: User):
    lang = await _current_lang(state, user)
    _, eq_id_str, category = call.data.split(":", 2)
    if eq_id_str.isdigit():
        eq_id = int(eq_id_str)
    else:
        eq = (await session.execute(select(Equipment).where(Equipment.code == eq_id_str))).scalar_one_or_none()
        if not eq:
            message = "Equipment not found." if lang == "en" else "Инвентарь не найден."
            await call.answer(message, show_alert=True)
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
    await call.message.edit_reply_markup(reply_markup=await build_equipment_items_kb(session, selected, category, lang))
    await call.answer()


@router.callback_query(OnboardingStates.equipment, F.data == "eq_done")
async def finish_equipment_onboarding(call: CallbackQuery, state: FSMContext, user: User):
    lang = await _current_lang(state, user)
    await state.set_state(OnboardingStates.training_days)
    text = (
        "📅 <b>Step 10 / 11 — Days per week</b>\n\nHow many days per week do you want to train?"
        if lang == "en"
        else "📅 <b>Шаг 10 / 11 — Дни в неделю</b>\n\nСколько дней в неделю хочешь тренироваться?"
    )
    await safe_edit_text(call.message, text, reply_markup=days_kb(lang), parse_mode="HTML")
    await call.answer()


@router.callback_query(OnboardingStates.training_days, F.data.startswith("cal:days:"))
async def step_duration(callback: CallbackQuery, state: FSMContext, user: User):
    lang = await _current_lang(state, user)
    await state.update_data(days_per_week=int(callback.data.split(":")[2]))
    await state.set_state(OnboardingStates.duration)
    text = (
        "⏱ <b>Step 11 / 11 — Duration</b>\n\nPreferred workout duration:"
        if lang == "en"
        else "⏱ <b>Шаг 11 / 11 — Длительность</b>\n\nЖелаемое время одной тренировки:"
    )
    await safe_edit_text(callback.message, text, reply_markup=duration_kb(lang), parse_mode="HTML")


@router.callback_query(OnboardingStates.duration, F.data.startswith("cal:dur:"))
async def ask_strength_calibration(callback: CallbackQuery, state: FSMContext, user: User, session: AsyncSession):
    duration = int(callback.data.split(":")[2])
    await state.update_data(preferred_duration_min=duration)
    await state.set_state(OnboardingStates.strength_calibration)
    lang = await _current_lang(state, user)
    await safe_edit_text(
        callback.message,
        strength_calibration_help(lang),
        reply_markup=strength_calibration_kb(lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(OnboardingStates.strength_calibration, F.data == "cal:strength:enter")
async def prompt_strength_lines(callback: CallbackQuery, state: FSMContext, user: User):
    lang = await _current_lang(state, user)
    if lang == "en":
        text = (
            "Send your working weights in one message.\n\n"
            "Examples:\n"
            "<code>Bench press 80x8</code>\n"
            "<code>Squat 100x5</code>\n"
            "<code>Back row 65x10</code>\n\n"
            "Use a normal hard working set, not a one-rep max."
        )
    else:
        text = (
            "Отправь рабочие веса одним сообщением.\n\n"
            "Примеры:\n"
            "<code>Жим лежа 80x8</code>\n"
            "<code>Присед 100x5</code>\n"
            "<code>Тяга на спину 65x10</code>\n\n"
            "Пиши обычный тяжелый рабочий подход, не разовый максимум."
        )
    await safe_edit_text(callback.message, text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(OnboardingStates.strength_calibration, F.data == "cal:strength:skip")
async def skip_strength_calibration(callback: CallbackQuery, state: FSMContext, user: User, session: AsyncSession):
    await _complete_onboarding(callback.message, state, user, session, strength_entries=[])
    await callback.answer()


@router.message(OnboardingStates.strength_calibration, F.text)
async def save_strength_lines(message: Message, state: FSMContext, user: User, session: AsyncSession):
    entries = await save_strength_calibration(session, user.id, message.text or "")
    if not entries:
        lang = await _current_lang(state, user)
        text = (
            "I could not recognize the weights. Try: <code>Bench press 80x8</code>, or press skip in the previous message."
            if lang == "en"
            else "Не смог распознать веса. Попробуй так: <code>Жим лежа 80x8</code>, или нажми пропуск в предыдущем сообщении."
        )
        await message.answer(text, parse_mode="HTML")
        return
    await _complete_onboarding(message, state, user, session, strength_entries=entries)


async def _complete_onboarding(
    event_message: Message,
    state: FSMContext,
    user: User,
    session: AsyncSession,
    strength_entries: list[dict],
):
    data = await state.get_data()
    duration = int(data["preferred_duration_min"])
    await state.clear()

    cal = process_calibration(
        experience_level=ExperienceLevel(data["experience_level"]),
        experience_months=data["experience_months"],
        age=data.get("age", 25),
        health_flags=data.get("health_flags", []),
        days_per_week=data["days_per_week"],
        preferred_duration_min=duration,
        goal=Goal(data["goal"]),
    )

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
        for key, value in pdata.items():
            setattr(profile, key, value)

    eq_ids = data.get("equipment_ids", [])
    bw_result = await session.execute(select(Equipment).where(Equipment.category == EquipmentCategory.none).limit(1))
    bodyweight = bw_result.scalar_one_or_none()
    if bodyweight and bodyweight.id not in eq_ids:
        eq_ids.append(bodyweight.id)

    for eq_id in eq_ids:
        exists = await session.execute(
            select(UserEquipment).where(UserEquipment.user_id == user.id, UserEquipment.equipment_id == eq_id)
        )
        if not exists.scalar_one_or_none():
            session.add(UserEquipment(user_id=user.id, equipment_id=eq_id))

    data["strength_calibration"] = strength_entries
    session.add(CalibrationAnswer(user_id=user.id, question_key="full_calibration", answer=data))
    await session.commit()

    lang = _lang(data.get("language") or user.language_code)
    goals_ru = {
        "mass_gain": "💪 Набор массы",
        "maintenance": "⚖️ Поддержка",
        "weight_loss": "🔥 Похудание",
        "cardio": "🏃 Кардио",
    }
    goals_en = {
        "mass_gain": "💪 Muscle gain",
        "maintenance": "⚖️ Maintenance",
        "weight_loss": "🔥 Fat loss",
        "cardio": "🏃 Cardio",
    }
    struct_label = (
        "Full body"
        if cal.training_structure.value == "fullbody"
        else f"Split — {cal.split_type.value if cal.split_type else ''}"
    )
    if lang == "ru":
        struct_label = (
            "Все тело (Fullbody)"
            if cal.training_structure.value == "fullbody"
            else f"Сплит — {cal.split_type.value if cal.split_type else ''}"
        )
    intensity_bar = "🟩" * cal.intensity_level + "⬜" * (5 - cal.intensity_level)

    if lang == "en":
        if strength_entries:
            saved = ", ".join(f"{item['label_en']} {item['weight_kg']:g}x{item['reps']}" for item in strength_entries)
            strength_text = f"🏋️ <b>Working weights:</b> saved ({saved})\n"
        else:
            strength_text = "🏋️ <b>Working weights:</b> first workout will be diagnostic\n"
        summary_text = (
            "✅ <b>Calibration complete!</b>\n\n"
            "Your training profile:\n\n"
            f"🎯 <b>Goal:</b> {goals_en.get(data['goal'], data['goal'])}\n"
            f"📊 <b>Structure:</b> {struct_label}\n"
            f"⚡ <b>Intensity:</b> {intensity_bar} ({cal.intensity_level}/5)\n"
            f"📅 <b>Days/week:</b> {cal.recommended_days_per_week}\n"
            f"⏱ <b>Duration:</b> {cal.recommended_duration_min} min\n\n"
            f"{strength_text}\n"
            "How it works: if weights were entered, I start from them. If not, the first workout collects signals through Hard/Easy buttons, and the next sessions get more accurate.\n\n"
            "Ready for the first workout? 💪"
        )
    else:
        if strength_entries:
            saved = ", ".join(f"{item['label_ru']} {item['weight_kg']:g}x{item['reps']}" for item in strength_entries)
            strength_text = f"🏋️ <b>Рабочие веса:</b> учтены ({saved})\n"
        else:
            strength_text = "🏋️ <b>Рабочие веса:</b> первая тренировка будет диагностической\n"
        summary_text = (
            "✅ <b>Калибровка завершена!</b>\n\n"
            "Твой профиль тренировок:\n\n"
            f"🎯 <b>Цель:</b> {goals_ru.get(data['goal'], data['goal'])}\n"
            f"📊 <b>Структура:</b> {struct_label}\n"
            f"⚡ <b>Интенсивность:</b> {intensity_bar} ({cal.intensity_level}/5)\n"
            f"📅 <b>Дней в нед.:</b> {cal.recommended_days_per_week}\n"
            f"⏱ <b>Длительность:</b> {cal.recommended_duration_min} мин\n\n"
            f"{strength_text}\n"
            "Как это работает: если веса введены, я начну от них. Если нет — первая тренировка соберет сигналы через кнопки «Тяжело» и «Легко», а следующие занятия станут точнее.\n\n"
            "Готов к первой тренировке? 💪"
        )

    await safe_edit_text(
        event_message,
        summary_text,
        reply_markup=main_menu_keyboard(lang=lang, telegram_id=user.telegram_id),
        parse_mode="HTML",
    )
