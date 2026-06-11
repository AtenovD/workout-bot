from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from bot.states.states import WorkoutStates
from bot.keyboards.main_menu import workout_modifier_keyboard, set_logging_keyboard

router = Router()


@router.message(Command("workout"))
@router.callback_query(F.data == "menu:workout")
async def start_workout(event, state: FSMContext):
    msg = event.message if isinstance(event, CallbackQuery) else event
    await state.set_state(WorkoutStates.choosing_modifier)
    text = (
        "🏋️ <b>Начинаем тренировку!</b>\n\n"
        "Как себя чувствуешь сегодня? Выбери режим:"
    )
    if isinstance(event, CallbackQuery):
        await msg.edit_text(text, reply_markup=workout_modifier_keyboard(), parse_mode="HTML")
    else:
        await msg.answer(text, reply_markup=workout_modifier_keyboard(), parse_mode="HTML")


@router.callback_query(F.data.startswith("modifier:"))
async def show_workout_overview(callback: CallbackQuery, state: FSMContext):
    modifier = callback.data.split(":")[1]
    await state.update_data(modifier=modifier)
    await state.set_state(WorkoutStates.overview)

    modifier_names = {"light": "🟢 Облегчённый", "normal": "⚪ Обычный", "hard": "🔴 Утяжелённый"}
    modifier_name = modifier_names.get(modifier, modifier)

    # TODO: generate actual workout from service
    await callback.message.edit_text(
        f"📋 <b>Обзор тренировки — {modifier_name}</b>\n\n"
        f"<b>Сегодня:</b> Fullbody\n"
        f"<b>Упражнений:</b> 6\n"
        f"<b>Примерное время:</b> 45 мин\n\n"
        f"1. Приседания со штангой — 4×8\n"
        f"2. Жим лёжа — 4×8\n"
        f"3. Тяга штанги в наклоне — 4×8\n"
        f"4. Жим гантелей стоя — 3×10\n"
        f"5. Подтягивания — 3×8\n"
        f"6. Планка — 3×60с\n",
        reply_markup=__import__('aiogram').types.InlineKeyboardMarkup(inline_keyboard=[
            [__import__('aiogram').types.InlineKeyboardButton(text="▶️ Начать", callback_data="workout:begin")],
            [__import__('aiogram').types.InlineKeyboardButton(text="🔄 Перегенерировать", callback_data="workout:regenerate")],
        ]),
        parse_mode="HTML",
    )
