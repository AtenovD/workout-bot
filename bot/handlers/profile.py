from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date

from models.user import User
from models.profile import Profile, Goal, ExperienceLevel
from models.body_measurement import BodyMeasurement
from bot.states.states import ProfileStates
from bot.keyboards.main_menu import main_menu_keyboard

router = Router()


def profile_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚖️ Обновить вес", callback_data="prof:update_weight")],
        [InlineKeyboardButton(text="🎯 Изменить цель", callback_data="prof:change_goal")],
        [InlineKeyboardButton(text="🔄 Перекалибровка", callback_data="prof:recalibrate")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:back")],
    ])


@router.message(Command("profile"))
@router.callback_query(F.data == "menu:profile")
async def show_profile(event, user: User, session: AsyncSession, **kwargs):
    msg = event.message if isinstance(event, CallbackQuery) else event

    profile_res = await session.execute(select(Profile).where(Profile.user_id == user.id))
    profile = profile_res.scalar_one_or_none()

    if not profile or not profile.calibrated_at:
        text = "Профиль не заполнен. Пройди калибровку: /start"
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🚀 Начать калибровку", callback_data="cal:start")]])
    else:
        goal_names = {"mass_gain": "Набор массы", "weight_loss": "Похудение", "maintenance": "Поддержание", "cardio": "Кардио / выносливость"}
        exp_names = {"beginner": "Новичок", "intermediate": "Средний", "advanced": "Продвинутый"}
        struct_names = {"fullbody": "Фулбоди", "split": "Сплит"}

        age = ""
        if profile.birth_date:
            age = f", {(date.today() - profile.birth_date).days // 365} лет"

        text = (
            f"👤 <b>Профиль</b>\n\n"
            f"📏 Рост: {profile.height_cm or '—'} см{age}\n"
            f"⚖️ Вес: {float(profile.current_weight_kg or 0):.1f} кг"
            + (f" → {float(profile.target_weight_kg):.1f} кг" if profile.target_weight_kg else "") + "\n"
            f"🎯 Цель: {goal_names.get(profile.goal.value if profile.goal else '', '—')}\n"
            f"💪 Опыт: {exp_names.get(profile.experience_level.value if profile.experience_level else '', '—')}\n"
            f"🏗 Тренировки: {struct_names.get(profile.training_structure.value if profile.training_structure else '', '—')}\n"
            f"⏱ Длительность: {profile.preferred_duration_min} мин"
        )
        kb = profile_menu_kb()

    if isinstance(event, CallbackQuery):
        await msg.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await msg.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "prof:update_weight")
async def ask_new_weight(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ProfileStates.entering_weight)
    await callback.message.edit_text(
        "Введи свой текущий вес (кг):\n_Например: 82.5_",
        parse_mode="Markdown",
    )


@router.message(ProfileStates.entering_weight, F.text)
async def save_new_weight(message: Message, state: FSMContext, user: User, session: AsyncSession):
    try:
        weight = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Некорректное значение. Введи число, например: 82.5")
        return

    profile_res = await session.execute(select(Profile).where(Profile.user_id == user.id))
    profile = profile_res.scalar_one_or_none()
    if profile:
        profile.current_weight_kg = weight

    session.add(BodyMeasurement(user_id=user.id, date=date.today(), weight_kg=weight))
    await session.commit()
    await state.clear()
    await message.answer(f"✅ Вес обновлён: {weight} кг", reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "prof:change_goal")
async def change_goal(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💪 Набор массы",   callback_data="goal:mass_gain")],
        [InlineKeyboardButton(text="🔥 Похудение",     callback_data="goal:weight_loss")],
        [InlineKeyboardButton(text="⚖️ Поддержание",  callback_data="goal:maintenance")],
        [InlineKeyboardButton(text="🏃 Кардио",        callback_data="goal:cardio")],
    ])
    await callback.message.edit_text("Выбери новую цель:", reply_markup=kb)


@router.callback_query(F.data.startswith("goal:"))
async def save_goal(callback: CallbackQuery, user: User, session: AsyncSession):
    goal_value = callback.data.split(":")[1]
    profile_res = await session.execute(select(Profile).where(Profile.user_id == user.id))
    profile = profile_res.scalar_one_or_none()
    if profile:
        profile.goal = Goal(goal_value)
        await session.commit()
    goal_names = {"mass_gain": "Набор массы", "weight_loss": "Похудение", "maintenance": "Поддержание", "cardio": "Кардио"}
    await callback.message.edit_text(
        f"✅ Цель изменена на: {goal_names.get(goal_value, goal_value)}",
        reply_markup=profile_menu_kb()
    )
