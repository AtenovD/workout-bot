from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.states.states import CalibrationStates
from bot.keyboards.main_menu import main_menu_keyboard
from models.user import User

router = Router()


def gender_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👨 Мужской", callback_data="gender:male"),
            InlineKeyboardButton(text="👩 Женский", callback_data="gender:female"),
        ]
    ])


def goal_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💪 Набор массы", callback_data="goal:mass_gain")],
        [InlineKeyboardButton(text="⚖️ Поддержка формы", callback_data="goal:maintenance")],
        [InlineKeyboardButton(text="🔥 Похудание", callback_data="goal:weight_loss")],
        [InlineKeyboardButton(text="🏃 Улучшение кардио", callback_data="goal:cardio")],
    ])


def experience_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆕 Никогда не тренировался", callback_data="exp:0")],
        [InlineKeyboardButton(text="📅 До 6 месяцев", callback_data="exp:3")],
        [InlineKeyboardButton(text="📆 6–24 месяца", callback_data="exp:12")],
        [InlineKeyboardButton(text="🏆 Больше 2 лет", callback_data="exp:30")],
    ])


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, user: User):
    # Check if already calibrated
    await state.set_state(CalibrationStates.welcome)
    name = message.from_user.first_name or "Привет"
    await message.answer(
        f"👋 <b>Привет, {name}!</b>\n\n"
        "Я — твой персональный AI-тренер. Я:\n"
        "• Узнаю твои цели и возможности\n"
        "• Создам тренировки под твой инвентарь\n"
        "• Буду вести тебя упражнение за упражнением\n"
        "• Отслежу прогресс и подниму нагрузку вовремя\n\n"
        "Пройдём быструю калибровку — займёт 2 минуты!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Поехали!", callback_data="calibration:start")]
        ]),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "calibration:start")
async def calibration_gender(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CalibrationStates.gender)
    await callback.message.edit_text(
        "👤 <b>Шаг 1/12</b>\n\nУкажи свой пол:",
        reply_markup=gender_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("gender:"))
async def calibration_age(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split(":")[1]
    await state.update_data(gender=gender)
    await state.set_state(CalibrationStates.age)
    await callback.message.edit_text(
        "🎂 <b>Шаг 2/12</b>\n\nСколько тебе лет?\n\nНапиши число (например: <code>28</code>):",
        parse_mode="HTML",
    )


@router.message(CalibrationStates.age)
async def calibration_height(message: Message, state: FSMContext):
    try:
        age = int(message.text.strip())
        if not 10 <= age <= 100:
            raise ValueError
    except ValueError:
        await message.answer("Введи корректный возраст (число от 10 до 100):")
        return
    await state.update_data(age=age)
    await state.set_state(CalibrationStates.height)
    await message.answer(
        "📏 <b>Шаг 3/12</b>\n\nКакой у тебя рост?\n\nНапиши в сантиметрах (например: <code>178</code>):",
        parse_mode="HTML",
    )


@router.message(CalibrationStates.height)
async def calibration_weight(message: Message, state: FSMContext):
    try:
        height = int(message.text.strip())
        if not 100 <= height <= 250:
            raise ValueError
    except ValueError:
        await message.answer("Введи рост в сантиметрах (от 100 до 250):")
        return
    await state.update_data(height_cm=height)
    await state.set_state(CalibrationStates.weight_current)
    await message.answer(
        "⚖️ <b>Шаг 4/12</b>\n\nСколько ты сейчас весишь?\n\nНапиши в кг (например: <code>75.5</code>):",
        parse_mode="HTML",
    )


@router.message(CalibrationStates.weight_current)
async def calibration_goal_weight(message: Message, state: FSMContext):
    try:
        weight = float(message.text.replace(",", ".").strip())
        if not 30 <= weight <= 300:
            raise ValueError
    except ValueError:
        await message.answer("Введи вес в кг (например: 75.5):")
        return
    await state.update_data(current_weight_kg=weight)
    await state.set_state(CalibrationStates.weight_target)
    await message.answer(
        "🎯 <b>Шаг 5/12</b>\n\nКакой вес хочешь достичь?\n\nНапиши в кг:",
        parse_mode="HTML",
    )


@router.message(CalibrationStates.weight_target)
async def calibration_goal(message: Message, state: FSMContext):
    try:
        weight = float(message.text.replace(",", ".").strip())
    except ValueError:
        await message.answer("Введи целевой вес в кг:")
        return
    await state.update_data(target_weight_kg=weight)
    await state.set_state(CalibrationStates.goal)
    await message.answer(
        "🏁 <b>Шаг 6/12</b>\n\nКакая у тебя главная цель?",
        reply_markup=goal_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("goal:"))
async def calibration_experience(callback: CallbackQuery, state: FSMContext):
    goal = callback.data.split(":")[1]
    await state.update_data(goal=goal)
    await state.set_state(CalibrationStates.experience)
    await callback.message.edit_text(
        "💪 <b>Шаг 7/12</b>\n\nКакой у тебя опыт тренировок?",
        reply_markup=experience_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("exp:"))
async def calibration_complete(callback: CallbackQuery, state: FSMContext):
    months = int(callback.data.split(":")[1])
    await state.update_data(experience_months=months)
    data = await state.get_data()
    await state.clear()

    # TODO: save profile to DB and run calibration service
    await callback.message.edit_text(
        f"✅ <b>Калибровка завершена!</b>\n\n"
        f"Я подготовил твой профиль:\n"
        f"• Цель: {data.get('goal', '—')}\n"
        f"• Опыт: {months} мес.\n"
        f"• Вес: {data.get('current_weight_kg', '—')} → {data.get('target_weight_kg', '—')} кг\n\n"
        f"Готов к первой тренировке? 💪",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
