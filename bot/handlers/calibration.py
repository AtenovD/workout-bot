from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date

from bot.states.states import OnboardingStates
from models.calibration import CalibrationAnswer
from models.user import User
from bot.keyboards.main_menu import main_menu_keyboard
from bot.utils.module_visuals import send_module_visual
from bot.utils.message_edit import safe_edit_text

router = Router()

CALIBRATION_QUESTIONS = [
    {
        "key": "training_days",
        "question": "Сколько дней в неделю ты готов тренироваться?",
        "options": [("2-3 дня", "2_3"), ("3-4 дня", "3_4"), ("4-5 дней", "4_5"), ("5+ дней", "5_plus")]
    },
    {
        "key": "goal",
        "question": "Какая у тебя основная цель?",
        "options": [("Набрать массу 💪", "bulk"), ("Похудеть 🔥", "cut"), ("Сила 🏋️", "strength"), ("Тонус/здоровье 🧘", "fitness")]
    },
    {
        "key": "split",
        "question": "Какой сплит тебе удобнее?",
        "options": [("Full Body 🏃", "full_body"), ("Верх/Низ 🔝", "upper_lower"), ("Push/Pull/Legs 🔄", "ppl"), ("Классический сплит 🗓️", "bro_split")]
    },
    {
        "key": "rest_pref",
        "question": "Какой отдых между подходами предпочитаешь?",
        "options": [("Короткий (30-60с) ⚡", "short"), ("Средний (60-90с) ⏱️", "medium"), ("Длинный (2-3 мин) 🐢", "long")]
    },
    {
        "key": "cardio",
        "question": "Добавлять кардио после силовой?",
        "options": [("Да, 10-15 мин 🏃‍♂️", "yes"), ("Нет, только силовая 🏋️", "no")]
    },
]

CAL_IDX = {}  # question_idx -> question

@router.message(F.text.in_({"📋 Калибровка", "📋 Calibration"}))
@router.callback_query(F.data == "menu:calibration")
async def start_calibration(event, state: FSMContext, user: User, session: AsyncSession):
    is_callback = isinstance(event, CallbackQuery)

    await state.clear()
    await state.update_data(cal_idx=0, cal_answers={})

    q = CALIBRATION_QUESTIONS[0]
    buttons = [[InlineKeyboardButton(text=label, callback_data=f"cal:a:{q['key']}:{val}")] for label, val in q["options"]]
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="menu:back")])

    text = f"📋 <b>Калибровка — вопрос 1 из {len(CALIBRATION_QUESTIONS)}</b>\n\n{q['question']}"

    await send_module_visual(event, "calibration", text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data.startswith("cal:a:"))
async def process_cal_answer(callback: CallbackQuery, state: FSMContext, user: User, session: AsyncSession):
    parts = callback.data.split(":")
    key, val = parts[2], parts[3]

    data = await state.get_data()
    idx = data.get("cal_idx", 0)
    answers = data.get("cal_answers", {})
    answers[key] = val

    # Save to DB
    session.add(CalibrationAnswer(
        user_id=user.id,
        question_key=key,
        answer={"key": key, "value": val, "date": str(date.today())}
    ))
    await session.commit()

    idx += 1

    if idx >= len(CALIBRATION_QUESTIONS):
        await state.clear()
        await safe_edit_text(callback.message,
            "✅ <b>Калибровка завершена!</b>\n\nТеперь тренировки будут подбираться с учётом твоих предпочтений.\n\nНачни тренировку через главное меню!",
            reply_markup=main_menu_keyboard(telegram_id=user.telegram_id),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    q = CALIBRATION_QUESTIONS[idx]
    buttons = [[InlineKeyboardButton(text=label, callback_data=f"cal:a:{q['key']}:{val}")] for label, val in q["options"]]
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="menu:back")])

    await state.update_data(cal_idx=idx, cal_answers=answers)
    await safe_edit_text(callback.message,
        f"📋 <b>Калибровка — вопрос {idx+1} из {len(CALIBRATION_QUESTIONS)}</b>\n\n{q['question']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()
