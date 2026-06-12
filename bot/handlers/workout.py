from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc, func
from datetime import datetime, date
from typing import List
import asyncio
import logging

from bot.states.states import WorkoutStates
from bot.keyboards.main_menu import main_menu_keyboard
from bot.keyboards.workout import modifier_kb
from models.workout import WorkoutSession, SessionStatus, SessionExercise, ExerciseSet
from models.exercise import Exercise, EquipmentCategory
from models.user_equipment import UserEquipment
from models.personal_record import PersonalRecord
from models.user import User
from models.gamification import UserXP, XPEvent

logger = logging.getLogger(__name__)
router = Router()

MODIFIER_LABELS = {"easy": "☀️ Лёгкая", "normal": "💪 Обычная", "hard": "🔥 Жёсткая"}
REST_TIMER_SEC = 90


# ─── Helpers ────────────────────────────────────────────────────────

def set_log_kb(se_id, set_num, reps, weight):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="−", callback_data=f"set:rm:{se_id}"),
         InlineKeyboardButton(text=f"🔁 {reps} повт.", callback_data=f"set:rs:{se_id}"),
         InlineKeyboardButton(text="+", callback_data=f"set:rp:{se_id}")],
        [InlineKeyboardButton(text="−2.5", callback_data=f"set:wm:{se_id}"),
         InlineKeyboardButton(text=f"⚖️ {float(weight):.1f} кг", callback_data=f"set:ws:{se_id}"),
         InlineKeyboardButton(text="+2.5", callback_data=f"set:wp:{se_id}")],
        [InlineKeyboardButton(text=f"✅ Подход {set_num} — выполнен!", callback_data=f"set:done:{se_id}")],
        [InlineKeyboardButton(text="😰 Тяжело", callback_data=f"set:hard:{se_id}"),
         InlineKeyboardButton(text="😊 Легко", callback_data=f"set:easy:{se_id}")],
        [InlineKeyboardButton(text="🔄 Заменить", callback_data=f"set:replace:{se_id}"),
         InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"ex:skip:{se_id}")],
    ])


def rest_kb(se_id, seconds_left):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🕒 Отдых: {seconds_left}с", callback_data="noop")],
        [InlineKeyboardButton(text="▶️ Готов!", callback_data=f"rest:done:{se_id}"),
         InlineKeyboardButton(text="⏭ Пропустить отдых", callback_data=f"rest:skip:{se_id}")],
    ])


def overview_kb(session_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Начать!", callback_data=f"wk:start:{session_id}")],
        [InlineKeyboardButton(text="🔄 Перегенерировать", callback_data=f"wk:regen:{session_id}")],
        [InlineKeyboardButton(text="💰 Выбрать интенсивность", callback_data="wk:choose_modifier")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="menu:main")],
    ])


async def send_exercise_photo(bot, chat_id, exercise, state):
    """Send exercise visual (photo/GIF) if available."""
    data = await state.get_data()
    sent = data.get("ex_photo_sent")
    if sent:
        return
    try:
        url = exercise.video_url or exercise.gif_url or exercise.photo_url
        if not url:
            return
        if exercise.video_url:
            await bot.send_video(chat_id, url, caption=f"📹 <i>{exercise.name_ru}</i>", parse_mode="HTML")
        elif exercise.gif_url:
            await bot.send_animation(chat_id, url, caption=f"🎥 <i>{exercise.name_ru}</i>", parse_mode="HTML")
        elif exercise.photo_url:
            await bot.send_photo(chat_id, url, caption=f"📷 <i>{exercise.name_ru}</i>", parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Failed to send exercise media for {exercise.id}: {e}")
    await state.update_data(ex_photo_sent=True)


async def send_rest_timer(bot, chat_id, se_id, message_id, seconds=REST_TIMER_SEC):
    """Start rest timer with countdown updates."""
    for s in range(seconds, 0, -5):
        await asyncio.sleep(5)
        try:
            await bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=rest_kb(se_id, s)
            )
        except Exception:
            break


# ─── Start Workout ─────────────────────────────────────────────────

@router.message(Command("workout"))
@router.callback_query(F.data == "menu:workout")
async def start_workout(event, state: FSMContext, user: User, session: AsyncSession, **kwargs):
    is_callback = isinstance(event, CallbackQuery)
    bot = event.bot if is_callback else event.bot
    chat_id = event.message.chat.id if is_callback else event.from_user.id

    await state.clear()
    await state.set_state(WorkoutStates.choosing_modifier)

    text = (
        "🏋️ <b>Тренировка</b>

"
        "Выбери интенсивность:"
    )
    if is_callback:
        await event.message.edit_text(text, reply_markup=modifier_kb(), parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=modifier_kb(), parse_mode="HTML")


@router.callback_query(F.data == "wk:choose_modifier", WorkoutStates.overview)
async def choose_modifier(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(WorkoutStates.choosing_modifier)
    await callback.message.edit_text(
        "🏋️ <b>Тренировка</b>

Выбери интенсивность:",
        reply_markup=modifier_kb(), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("modifier:"), WorkoutStates.choosing_modifier)
async def begin_workout(callback: CallbackQuery, state: FSMContext, user: User, session: AsyncSession):
    modifier = callback.data.split(":")[1]

    # Get user equipment
    ue_res = await session.execute(
        select(UserEquipment.equipment_id).where(UserEquipment.user_id == user.id, UserEquipment.has_it == True)
    )
    user_eq_ids = set(ue_res.scalars().all())

    # Filter exercises: none-category always allowed, others need matching equipment
    from sqlalchemy import or_
    ex_res = await session.execute(
        select(Exercise).where(
            Exercise.is_active == True,
            or_(
                Exercise.equipment_category == EquipmentCategory.none,
                Exercise.required_equipment_id.in_(user_eq_ids) if user_eq_ids else False,
            )
        ).order_by(Exercise.muscle_group, Exercise.name_ru)
    )
    available = ex_res.scalars().all()

    if len(available) < 4:
        await callback.message.edit_text(
            "⚠️ Недостаточно упражнений для твоего инвентаря.
Добавь инвентарь в настройках.",
            reply_markup=main_menu_keyboard()
        )
        await callback.answer()
        return

    # Simple plan: pick 4-6 exercises across muscle groups
    import random
    random.shuffle(available)
    muscle_groups = {}
    for ex in available:
        mg = ex.muscle_group or "general"
        if mg not in muscle_groups or len(muscle_groups[mg]) < 2:
            muscle_groups.setdefault(mg, []).append(ex)
    plan = []
    for mg_exs in muscle_groups.values():
        plan.extend(mg_exs[:1])
    if len(plan) < 4:
        plan = available[:6]

    plan = plan[:6]

    # Create workout session
    ws = WorkoutSession(
        user_id=user.id,
        status=SessionStatus.planned,
        modifier=modifier,
        started_at=datetime.utcnow()
    )
    session.add(ws)
    await session.flush()

    for i, ex in enumerate(plan):
        se = SessionExercise(
            session_id=ws.id,
            exercise_id=ex.id,
            order_index=i,
            target_sets=4 if modifier == "hard" else 3,
            target_reps=8 if modifier == "hard" else 10 if modifier == "normal" else 12,
            target_weight_kg=0.0
        )
        session.add(se)

    await session.commit()

    # Show overview
    ex_list = "
".join([f"{i+1}. {ex.name_ru} — {4 if modifier=='hard' else 3}×{8 if modifier=='hard' else 10 if modifier=='normal' else 12}"
                         for i, ex in enumerate(plan)])
    await state.update_data(workout_session_id=ws.id)
    await state.set_state(WorkoutStates.overview)
    await callback.message.edit_text(
        f"📋 <b>План тренировки</b> ({MODIFIER_LABELS[modifier]})

{ex_list}",
        reply_markup=overview_kb(ws.id),
        parse_mode="HTML"
    )
    await callback.answer()


# ─── Exercise Flow ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith("wk:start:"))
async def begin_exercise_flow(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    session_id = int(callback.data.split(":")[2])
    ws = await session.get(WorkoutSession, session_id)
    if not ws:
        await callback.answer("Сессия не найдена.")
        return

    ws.status = SessionStatus.in_progress
    await session.commit()

    first_res = await session.execute(
        select(SessionExercise).where(SessionExercise.session_id == session_id, SessionExercise.is_completed == False)
        .order_by(asc(SessionExercise.order_index)).limit(1)
    )
    first_se = first_res.scalar()

    if not first_se:
        await callback.message.edit_text("⚠️ Нет упражнений в плане.", reply_markup=main_menu_keyboard())
        await callback.answer()
        return

    ex = await session.get(Exercise, first_se.exercise_id)
    await state.update_data(workout_session_id=session_id, current_set=1, current_reps=None, current_weight=None, ex_photo_sent=False)
    await state.set_state(WorkoutStates.in_exercise)

    await callback.message.edit_text(
        f"▶️ <b>{ex.name_ru}</b>
Подход 1 из {first_se.target_sets} · "
        f"{first_se.target_reps} повт. · {first_se.target_weight_kg or 0:.1f} кг",
        reply_markup=set_log_kb(first_se.id, 1, first_se.target_reps, first_se.target_weight_kg or 0.0),
        parse_mode="HTML"
    )

    # Send exercise photo/GIF
    await send_exercise_photo(callback.bot, callback.message.chat.id, ex, state)
    await callback.answer()


@router.callback_query(F.data.startswith("set:done:"), WorkoutStates.in_exercise)
async def set_done(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    se_id = int(callback.data.split(":")[2])
    data = await state.get_data()
    se = await session.get(SessionExercise, se_id)
    reps = data.get("current_reps") or se.target_reps
    weight = data.get("current_weight") if data.get("current_weight") is not None else (se.target_weight_kg or 0.0)
    current_set = data.get("current_set", 1)

    session.add(ExerciseSet(session_exercise_id=se_id, set_number=current_set, reps_done=reps, weight_kg=weight))

    if current_set >= se.target_sets:
        se.is_completed = True
        await session.commit()

        # Find next incomplete exercise
        next_res = await session.execute(
            select(SessionExercise).where(
                SessionExercise.session_id == se.session_id,
                SessionExercise.is_completed == False
            ).order_by(asc(SessionExercise.order_index)).limit(1)
        )
        next_se = next_res.scalar()

        if not next_se:
            # All done
            await finish_workout(callback, state, await session.merge(await session.get(User, (await state.get_data()).get("user_id"))), session)
            return

        # Show rest timer
        ex = await session.get(Exercise, next_se.exercise_id)
        await state.update_data(current_set=1, current_reps=None, current_weight=None, ex_photo_sent=False)
        await state.set_state(WorkoutStates.in_exercise)

        rest_msg = await callback.message.edit_text(
            f"🕒 <b>Отдых {REST_TIMER_SEC}с</b>

"
            f"Следующее: <b>{ex.name_ru}</b>",
            reply_markup=rest_kb(se_id, REST_TIMER_SEC),
            parse_mode="HTML"
        )

        # Start async rest timer
        asyncio.create_task(send_rest_timer(callback.bot, callback.message.chat.id, se_id, rest_msg.message_id))
        await callback.answer()
    else:
        # Next set in same exercise
        next_set = current_set + 1
        se.target_reps = reps
        se.target_weight_kg = weight
        await state.update_data(current_set=next_set)
        await session.commit()

        ex = await session.get(Exercise, se.exercise_id)
        await callback.message.edit_text(
            f"<b>{ex.name_ru}</b>
Подход {next_set} из {se.target_sets} · "
            f"{se.target_reps} повт. · {se.target_weight_kg or 0:.1f} кг",
            reply_markup=set_log_kb(se_id, next_set, se.target_reps, se.target_weight_kg or 0.0),
            parse_mode="HTML"
        )
        await callback.answer()


@router.callback_query(F.data.startswith("rest:done:"))
async def rest_done(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    se_id = int(callback.data.split(":")[2])
    se = await session.get(SessionExercise, se_id)
    ex = await session.get(Exercise, se.exercise_id)

    await state.update_data(ex_photo_sent=False)
    await callback.message.edit_text(
        f"▶️ <b>{ex.name_ru}</b>
Подход 1 из {se.target_sets} · "
        f"{se.target_reps} повт. · {se.target_weight_kg or 0:.1f} кг",
        reply_markup=set_log_kb(se_id, 1, se.target_reps, se.target_weight_kg or 0.0),
        parse_mode="HTML"
    )
    # Send exercise photo/GIF
    await send_exercise_photo(callback.bot, callback.message.chat.id, ex, state)
    await callback.answer()


@router.callback_query(F.data.startswith("rest:skip:"))
async def rest_skip(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    se_id = int(callback.data.split(":")[2])
    se = await session.get(SessionExercise, se_id)
    ex = await session.get(Exercise, se.exercise_id)

    await state.update_data(ex_photo_sent=False)
    await callback.message.edit_text(
        f"▶️ <b>{ex.name_ru}</b>
Подход 1 из {se.target_sets} · "
        f"{se.target_reps} повт. · {se.target_weight_kg or 0:.1f} кг",
        reply_markup=set_log_kb(se_id, 1, se.target_reps, se.target_weight_kg or 0.0),
        parse_mode="HTML"
    )
    await send_exercise_photo(callback.bot, callback.message.chat.id, ex, state)
    await callback.answer()


# ─── Adjust Values ────────────────────────────────────────────

@router.callback_query(F.data.startswith("set:rs:") | F.data.startswith("set:rm:") | F.data.startswith("set:rp:") |
                       F.data.startswith("set:ws:") | F.data.startswith("set:wm:") | F.data.startswith("set:wp:"),
                       WorkoutStates.in_exercise)
async def adjust_values(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    parts = callback.data.split(":")
    action = f"{parts[1]}:{parts[2]}"
    se_id = int(parts[3])
    data = await state.get_data()
    reps = data.get("current_reps") or 10
    weight = data.get("current_weight") or 0.0
    current_set = data.get("current_set", 1)

    match action:
        case "rp": reps += 1
        case "rm": reps = max(1, reps - 1)
        case "wp": weight += 2.5
        case "wm": weight = max(0.0, round(weight - 2.5, 2))

    await state.update_data(current_reps=reps, current_weight=weight)
    await callback.message.edit_reply_markup(
        reply_markup=set_log_kb(se_id, current_set, reps, weight)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ex:skip:"))
async def skip_exercise(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    se_id = int(callback.data.split(":")[2])
    se = await session.get(SessionExercise, se_id)
    se.is_completed = True
    await session.commit()

    next_res = await session.execute(
        select(SessionExercise).where(
            SessionExercise.session_id == se.session_id,
            SessionExercise.is_completed == False
        ).order_by(asc(SessionExercise.order_index)).limit(1)
    )
    next_se = next_res.scalar()

    if not next_se:
        await finish_workout(callback, state, await session.merge(await session.get(User, (await state.get_data()).get("user_id"))), session)
        return

    ex = await session.get(Exercise, next_se.exercise_id)
    await state.update_data(current_set=1, current_reps=None, current_weight=None, ex_photo_sent=False)
    await callback.message.edit_text(
        f"▶️ <b>{ex.name_ru}</b>
Подход 1 из {next_se.target_sets} · "
        f"{next_se.target_reps} повт. · {next_se.target_weight_kg or 0:.1f} кг",
        reply_markup=set_log_kb(next_se.id, 1, next_se.target_reps, next_se.target_weight_kg or 0.0),
        parse_mode="HTML"
    )
    await send_exercise_photo(callback.bot, callback.message.chat.id, ex, state)
    await callback.answer()


# ─── Restore/Abort/Regen ───────────────────────────────

@router.callback_query(F.data.startswith("wk:resume:"))
async def resume_workout(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    session_id = int(callback.data.split(":")[2])
    ws = await session.get(WorkoutSession, session_id)
    if not ws:
        await callback.answer("Сессия не найдена.")
        return
    ws.status = SessionStatus.in_progress
    await session.commit()
    await state.update_data(workout_session_id=session_id)
    await state.set_state(WorkoutStates.in_exercise)

    res2 = await session.execute(
        select(SessionExercise).where(SessionExercise.session_id == session_id, SessionExercise.is_completed == False)
        .order_by(asc(SessionExercise.order_index))
    )
    se = res2.scalars().first()
    if not se:
        await callback.message.edit_text("Все упражнения выполнены!")
        return
    ex = await session.get(Exercise, se.exercise_id)
    await state.update_data(current_set=1, current_reps=None, current_weight=None, ex_photo_sent=False)
    await callback.message.edit_text(
        f"▶️ <b>{ex.name_ru}</b>
Подход 1 из {se.target_sets} · {se.target_reps} повт. · {se.target_weight_kg or 0:.1f} кг",
        reply_markup=set_log_kb(se.id, 1, se.target_reps, se.target_weight_kg or 0.0),
        parse_mode="HTML"
    )
    await send_exercise_photo(callback.bot, callback.message.chat.id, ex, state)
    await callback.answer()


@router.callback_query(F.data.startswith("wk:abort:"))
async def abort_workout(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    session_id = int(callback.data.split(":")[2])
    ws = await session.get(WorkoutSession, session_id)
    if ws:
        ws.status = SessionStatus.skipped
        ws.completed_at = datetime.utcnow()
        await session.commit()
    await state.clear()
    await callback.message.edit_text(
        "❌ Тренировка завершена досрочно. Возвращайся скорее! 💪",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("wk:regen:"))
async def regen_workout(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    session_id = data.get("workout_session_id")
    if session_id:
        old_ws = await session.get(WorkoutSession, session_id)
        if old_ws:
            old_ws.status = SessionStatus.skipped
            await session.commit()
    await state.clear()
    await state.set_state(WorkoutStates.choosing_modifier)
    await callback.message.edit_text(
        "🔄 <b>Перегенерируем!</b>

Выбери интенсивность:",
        reply_markup=modifier_kb(), parse_mode="HTML"
    )
    await callback.answer()


# ─── Replace Exercise ─────────────────────────────────────

@router.callback_query(F.data.startswith("set:replace:"))
async def replace_exercise(callback: CallbackQuery, state: FSMContext, session: AsyncSession, user: User):
    from models.exercise_alternatives import ExerciseAlternative
    se_id = int(callback.data.split(":")[2])
    se = await session.get(SessionExercise, se_id)
    if not se:
        await callback.answer("Упражнение не найдено.")
        return
    ex = await session.get(Exercise, se.exercise_id)
    alt_res = await session.execute(select(ExerciseAlternative).where(ExerciseAlternative.exercise_id == se.exercise_id))
    alternatives = alt_res.scalars().all()

    eq_res = await session.execute(select(UserEquipment.equipment_id).where(UserEquipment.user_id == user.id, UserEquipment.has_it == True))
    user_eq_ids = set(eq_res.scalars().all())

    buttons = []
    for alt in alternatives:
        alt_ex = await session.get(Exercise, alt.alternative_exercise_id)
        if not alt_ex or not alt_ex.is_active:
            continue
        if alt_ex.equipment_category == EquipmentCategory.none or alt_ex.required_equipment_id in user_eq_ids:
            buttons.append([InlineKeyboardButton(text=f"🔄 {alt_ex.name_ru}", callback_data=f"set:do_replace:{se_id}:{alt_ex.id}")])

    if not buttons:
        await callback.answer("Нет доступных замен с твоим инвентарём.", show_alert=True)
        return

    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data=f"set:cancel_replace:{se_id}")])
    await callback.message.edit_text(
        f"🔄 Замена для <b>{ex.name_ru}</b>
Выбери альтернативу:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set:do_replace:"))
async def do_replace_exercise(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    parts = callback.data.split(":")
    se_id, new_ex_id = int(parts[2]), int(parts[3])
    se = await session.get(SessionExercise, se_id)
    new_ex = await session.get(Exercise, new_ex_id)
    if not se or not new_ex:
        await callback.answer("Ошибка замены.")
        return
    se.exercise_id = new_ex_id
    await session.commit()
    data = await state.get_data()
    cs = data.get("current_set", 1)
    await state.update_data(current_reps=None, current_weight=None, ex_photo_sent=False)
    await callback.message.edit_text(
        f"✅ Заменено на <b>{new_ex.name_ru}</b>
Подход {cs} из {se.target_sets} · {se.target_reps} повт. · {se.target_weight_kg or 0:.1f} кг",
        reply_markup=set_log_kb(se_id, cs, se.target_reps, se.target_weight_kg or 0.0), parse_mode="HTML"
    )
    await send_exercise_photo(callback.bot, callback.message.chat.id, new_ex, state)
    await callback.answer()


@router.callback_query(F.data.startswith("set:cancel_replace:"))
async def cancel_replace(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    se_id = int(callback.data.split(":")[2])
    se = await session.get(SessionExercise, se_id)
    ex = await session.get(Exercise, se.exercise_id)
    data = await state.get_data()
    cs = data.get("current_set", 1)
    reps = data.get("current_reps") or se.target_reps
    weight = data.get("current_weight") if data.get("current_weight") is not None else (se.target_weight_kg or 0.0)
    await callback.message.edit_text(
        f"<b>{ex.name_ru}</b>
Подход {cs} из {se.target_sets} · {reps} повт. · {weight:.1f} кг",
        reply_markup=set_log_kb(se_id, cs, reps, weight), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set:hard:"))
async def set_too_hard(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    se_id = int(callback.data.split(":")[2])
    se = await session.get(SessionExercise, se_id)
    ex = await session.get(Exercise, se.exercise_id)
    data = await state.get_data()
    cs = data.get("current_set", 1)
    weight = data.get("current_weight") if data.get("current_weight") is not None else (se.target_weight_kg or 0.0)
    reps = data.get("current_reps") or se.target_reps
    step = 2.5 if ex.exercise_type and ex.exercise_type.value == "compound" else 1.25
    new_weight = max(0.0, round(weight - step, 2))
    new_reps = max(1, reps - 1)
    se.target_weight_kg = new_weight
    await state.update_data(current_weight=new_weight, current_reps=new_reps, feedback_rpe=9)
    await session.commit()
    await callback.message.edit_reply_markup(reply_markup=set_log_kb(se_id, cs, new_reps, new_weight))
    await callback.answer(f"⬇️ Снизил до {new_weight:.1f} кг / {new_reps} повт.")


@router.callback_query(F.data.startswith("set:easy:"))
async def set_too_easy(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    se_id = int(callback.data.split(":")[2])
    se = await session.get(SessionExercise, se_id)
    ex = await session.get(Exercise, se.exercise_id)
    data = await state.get_data()
    cs = data.get("current_set", 1)
    weight = data.get("current_weight") if data.get("current_weight") is not None else (se.target_weight_kg or 0.0)
    reps = data.get("current_reps") or se.target_reps
    step = 2.5 if ex.exercise_type and ex.exercise_type.value == "compound" else 1.25
    new_weight = round(weight + step, 2)
    new_reps = reps + 1
    se.target_weight_kg = new_weight
    await state.update_data(current_weight=new_weight, current_reps=new_reps, feedback_rpe=6)
    await session.commit()
    await callback.message.edit_reply_markup(reply_markup=set_log_kb(se_id, cs, new_reps, new_weight))
    await callback.answer(f"⬆️ Поднял до {new_weight:.1f} кг / {new_reps} повт.")


# ─── Finish Workout ──────────────────────────────────────────────

async def finish_workout(callback: CallbackQuery, state: FSMContext, user: User, session: AsyncSession):
    data = await state.get_data()
    session_id = data.get("workout_session_id")
    ws = await session.get(WorkoutSession, session_id) if session_id else None

    if ws:
        ws.status = SessionStatus.completed
        ws.completed_at = datetime.utcnow()
        await session.commit()

    await state.clear()

    # ─── PR Detection ───
    pr_lines: List[str] = []
    if session_id:
        sets_res = await session.execute(
            select(
                SessionExercise.exercise_id,
                ExerciseSet.weight_kg,
                ExerciseSet.reps_done
            ).join(
                ExerciseSet, ExerciseSet.session_exercise_id == SessionExercise.id
            ).where(
                SessionExercise.session_id == session_id
            )
        )
        rows = sets_res.all()

        for ex_id, weight, reps in rows:
            if not weight or weight <= 0:
                continue
            existing_pr = await session.execute(
                select(PersonalRecord).where(
                    PersonalRecord.user_id == user.id,
                    PersonalRecord.exercise_id == ex_id
                ).order_by(PersonalRecord.weight_kg.desc()).limit(1)
            )
            pr = existing_pr.scalar()
            if not pr or weight > pr.weight_kg:
                session.add(PersonalRecord(
                    user_id=user.id,
                    exercise_id=ex_id,
                    weight_kg=weight,
                    reps=reps,
                    recorded_at=datetime.utcnow()
                ))
                ex = await session.get(Exercise, ex_id)
                pr_lines.append(
                    f"🏆 Рекорд в <b>{ex.name_ru if ex else 'упражнении'}</b>: {weight:.1f} кг!"
                )
        await session.commit()

    # XP award
    xp_awarded = 10
    try:
        xp_rec = await session.execute(
            select(UserXP).where(UserXP.user_id == user.id)
        )
        xp = xp_rec.scalar()
        if xp:
            xp.xp += xp_awarded
        else:
            session.add(UserXP(user_id=user.id, xp=xp_awarded))
        await session.commit()
    except Exception:
        pass

    text = (
        f"✅ <b>Тренировка завершена!</b>

"
        f"⭐️ +{xp_awarded} XP"
    )
    if pr_lines:
        text += "

" + "
".join(pr_lines)

    await callback.message.edit_text(text, reply_markup=main_menu_keyboard(), parse_mode="HTML")
    await callback.answer()
