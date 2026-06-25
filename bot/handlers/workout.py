from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc, func
from datetime import datetime, date

from bot.states.states import WorkoutStates
from bot.keyboards.main_menu import main_menu_keyboard
from bot.utils.module_visuals import send_module_visual
from models.user import User
from models.profile import Profile
from models.workout import WorkoutSession, SessionExercise, ExerciseSet, SessionStatus, DifficultyModifier
from models.gamification import UserStats
from models.challenge import UserChallenge
from models.exercise import Exercise
from services.gamification import calculate_xp, get_level_from_xp, get_title
from services.calories import calculate_calories_burned, DEFAULT_MET
from services.pr_detection import detect_prs
from services.plateau_detection import check_and_apply_plateau
from services.deload_on_return import apply_return_deload
from services.rest_timer import run_rest_timer
from services.workout_summary import build_workout_summary, format_summary_message
import asyncio
from bot.utils.message_edit import safe_edit_text

router = Router()


def modifier_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Облегчённый", callback_data="mod:light")],
        [InlineKeyboardButton(text="⚪ Обычный", callback_data="mod:normal")],
        [InlineKeyboardButton(text="🔴 Утяжелённый", callback_data="mod:hard")],
    ])

def overview_kb(session_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Начать", callback_data=f"wk:begin:{session_id}")],
        [InlineKeyboardButton(text="🔄 Перегенерировать", callback_data=f"wk:regen:{session_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:back")],
    ])

def set_log_kb(se_id, set_num, reps, weight, technique_url=None):
    rows = [
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
         InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"set:skip:{se_id}")],
    ]
    if technique_url:
        rows.append([InlineKeyboardButton(text="🎞 Техника", url=technique_url)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def exercise_technique_url(ex):
    return getattr(ex, "gif_url", None) or getattr(ex, "photo_url", None) or getattr(ex, "video_url", None)

def rest_kb(se_id, next_set):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💪 Следующий подход", callback_data=f"rest:next:{se_id}:{next_set}")],
        [InlineKeyboardButton(text="⏭ Пропустить отдых", callback_data=f"rest:skip:{se_id}:{next_set}")],
    ])

def exercise_done_kb(next_se_id):
    if next_se_id:
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="➡️ Следующее упражнение", callback_data=f"ex:next:{next_se_id}")]])
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏁 Завершить тренировку", callback_data="wk:finish")]])


@router.message(Command("workout"))
@router.callback_query(F.data == "menu:workout")
async def start_workout(event, state: FSMContext, user: User, session: AsyncSession, **kwargs):
    msg = event.message if isinstance(event, CallbackQuery) else event
    existing = await session.execute(
        select(WorkoutSession).where(WorkoutSession.user_id == user.id,
                                     WorkoutSession.status == SessionStatus.in_progress).limit(1)
    )
    active = existing.scalar_one_or_none()
    if active:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Продолжить", callback_data=f"wk:resume:{active.id}")],
            [InlineKeyboardButton(text="❌ Завершить досрочно", callback_data=f"wk:abort:{active.id}")],
        ])
        await msg.answer("У тебя есть незавершённая тренировка. Продолжить?", reply_markup=kb)
        return
    await state.set_state(WorkoutStates.choosing_modifier)
    text = "🏋️ <b>Начинаем тренировку!</b>\n\nКак себя чувствуешь сегодня?"
    await send_module_visual(event, "workout", text, reply_markup=modifier_kb())


@router.callback_query(F.data.startswith("mod:"))
async def choose_modifier(callback: CallbackQuery, state: FSMContext, user: User, session: AsyncSession):
    modifier = callback.data.split(":")[1]
    p = await session.execute(select(Profile).where(Profile.user_id == user.id))
    profile = p.scalar_one_or_none()
    if not profile or not profile.calibrated_at:
        await safe_edit_text(callback.message, "Сначала пройди калибровку: /start")
        return
    from models.user_equipment import UserEquipment
    eq_res = await session.execute(select(UserEquipment).where(UserEquipment.user_id == user.id, UserEquipment.has_it == True))
    eq_ids = [ue.equipment_id for ue in eq_res.scalars().all()]
    ws = WorkoutSession(user_id=user.id, status=SessionStatus.planned,
                        difficulty_modifier=DifficultyModifier(modifier), scheduled_date=date.today())
    session.add(ws)
    await session.flush()
    from services.workout_generator import generate_workout_session
    exercises = await generate_workout_session(session=session, profile=profile,
                                               user_equipment_ids=eq_ids,
                                               workout_session_id=ws.id, modifier=modifier)
    await session.commit()
    await session.refresh(ws)
    mod_names = {"light": "🟢 Облегчённый", "normal": "⚪ Обычный", "hard": "🔴 Утяжелённый"}
    ex_list = "\n".join(f"{i+1}. {e.name_ru} — {se.target_sets}×{se.target_reps} · {se.target_weight_kg or 0:.1f} кг"
                          for i, (se, e) in enumerate(exercises))
    total_time = sum(se.target_sets * (45 + se.rest_seconds) for se, _ in exercises) // 60 + 10
    await state.update_data(workout_session_id=ws.id)
    await state.set_state(WorkoutStates.overview)
    await safe_edit_text(callback.message,
        f"📋 <b>{mod_names[modifier]}</b>\n\n{ex_list}\n\n⏱ ~{total_time} мин",
        reply_markup=overview_kb(ws.id), parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("wk:begin:"))
async def begin_workout(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    session_id = int(callback.data.split(":")[2])
    ws = await session.get(WorkoutSession, session_id)
    ws.status = SessionStatus.in_progress
    ws.started_at = datetime.utcnow()
    await session.commit()
    se_res = await session.execute(
        select(SessionExercise).where(SessionExercise.session_id == session_id,
                                       SessionExercise.is_completed == False)
        .order_by(asc(SessionExercise.order_index)).limit(1)
    )
    first_se = se_res.scalar_one_or_none()
    if not first_se:
        await safe_edit_text(callback.message, "Список упражнений пуст.")
        return
    ex = await session.get(Exercise, first_se.exercise_id)
    await state.update_data(current_set=1)
    await state.set_state(WorkoutStates.logging_set)

    # Send exercise media if available
    if getattr(ex, 'gif_url', None):
        try:
            await callback.message.answer_animation(ex.gif_url, caption=f"<b>{ex.name_ru}</b>", parse_mode="HTML")
        except Exception:
            pass
    elif getattr(ex, 'photo_url', None):
        try:
            await callback.message.answer_photo(ex.photo_url, caption=f"<b>{ex.name_ru}</b>", parse_mode="HTML")
        except Exception:
            pass
    await safe_edit_text(callback.message,
        f"<b>{ex.name_ru}</b>\nПодход 1 из {first_se.target_sets} · "
        f"{first_se.target_reps} повт. · {first_se.target_weight_kg or 0:.1f} кг",
        reply_markup=set_log_kb(first_se.id, 1, first_se.target_reps, first_se.target_weight_kg or 0.0, exercise_technique_url(ex)),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("set:done:"))
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
        next_res = await session.execute(
            select(SessionExercise).where(SessionExercise.session_id == se.session_id,
                                           SessionExercise.is_completed == False)
            .order_by(asc(SessionExercise.order_index)).limit(1)
        )
        next_se = next_res.scalar_one_or_none()
        await state.update_data(current_set=1, current_reps=None, current_weight=None)
        await callback.message.edit_reply_markup(reply_markup=exercise_done_kb(next_se.id if next_se else None))
        await callback.answer("✅ Упражнение выполнено!")
    else:
        await session.commit()
        next_set = current_set + 1
        await state.update_data(current_set=next_set, current_reps=None, current_weight=None)
        asyncio.create_task(run_rest_timer(callback.bot, callback.message.chat.id, se_id, next_set, se.rest_seconds or 90))
        await callback.message.edit_reply_markup(reply_markup=rest_kb(se_id, next_set))
        await callback.answer(f"✅ Подход {current_set} засчитан! Отдыхай {se.rest_seconds or 90} сек.")


@router.callback_query(F.data.startswith("set:rm:") | F.data.startswith("set:rp:") |
                        F.data.startswith("set:wm:") | F.data.startswith("set:wp:"))
async def adjust_values(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    parts = callback.data.split(":")
    action, se_id = parts[1], int(parts[2])
    se = await session.get(SessionExercise, se_id)
    data = await state.get_data()
    current_set = data.get("current_set", 1)
    reps = int(data.get("current_reps") or se.target_reps or 1)
    weight = data.get("current_weight") if data.get("current_weight") is not None else (se.target_weight_kg or 0.0)
    weight = float(weight or 0.0)
    if action == "rm": reps = max(1, reps - 1)
    elif action == "rp": reps = reps + 1
    elif action == "wm": weight = max(0.0, round(weight - 2.5, 2))
    elif action == "wp": weight = round(weight + 2.5, 2)
    await state.update_data(current_reps=reps, current_weight=weight)
    ex = await session.get(Exercise, se.exercise_id)
    await callback.message.edit_reply_markup(reply_markup=set_log_kb(se_id, current_set, reps, weight, exercise_technique_url(ex)))
    await callback.answer()


@router.callback_query(F.data.startswith("set:rs:") | F.data.startswith("set:ws:"))
async def set_display_value(callback: CallbackQuery):
    await callback.answer("Используй − / + рядом с показателем.")


@router.callback_query(F.data.startswith("rest:"))
async def rest_done(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    parts = callback.data.split(":")
    se_id, next_set = int(parts[2]), int(parts[3])
    se = await session.get(SessionExercise, se_id)
    ex = await session.get(Exercise, se.exercise_id)
    await state.update_data(current_set=next_set)
    await safe_edit_text(callback.message,
        f"<b>{ex.name_ru}</b>\nПодход {next_set} из {se.target_sets} · "
        f"{se.target_reps} повт. · {se.target_weight_kg or 0:.1f} кг",
        reply_markup=set_log_kb(se_id, next_set, se.target_reps, se.target_weight_kg or 0.0, exercise_technique_url(ex)),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("ex:next:"))
async def next_exercise(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    se_id = int(callback.data.split(":")[2])
    se = await session.get(SessionExercise, se_id)
    ex = await session.get(Exercise, se.exercise_id)
    await state.update_data(current_set=1, current_reps=None, current_weight=None)
    await callback.message.answer(
        f"<b>{ex.name_ru}</b>\nПодход 1 из {se.target_sets} · "
        f"{se.target_reps} повт. · {se.target_weight_kg or 0:.1f} кг",
        reply_markup=set_log_kb(se_id, 1, se.target_reps, se.target_weight_kg or 0.0, exercise_technique_url(ex)),
        parse_mode="HTML"
    )



@router.callback_query(F.data.startswith("wk:resume:"))
async def resume_workout(callback, state, session):
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
        select(SessionExercise)
        .where(SessionExercise.session_id == session_id, SessionExercise.is_completed == False)
        .order_by(asc(SessionExercise.order_index))
    )
    se = res2.scalars().first()
    if not se:
        await safe_edit_text(callback.message, "Все упражнения выполнены!")
        return
    ex = await session.get(Exercise, se.exercise_id)
    await state.update_data(current_set=1, current_reps=None, current_weight=None)
    await safe_edit_text(callback.message,
        f"▶️ <b>{ex.name_ru}</b>\nПодход 1 из {se.target_sets} · {se.target_reps} повт. · {se.target_weight_kg or 0:.1f} кг",
        reply_markup=set_log_kb(se.id, 1, se.target_reps, se.target_weight_kg or 0.0, exercise_technique_url(ex)),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("wk:abort:"))
async def abort_workout(callback, state, session):
    session_id = int(callback.data.split(":")[2])
    ws = await session.get(WorkoutSession, session_id)
    if ws:
        ws.status = SessionStatus.skipped
        ws.completed_at = datetime.utcnow()
        await session.commit()
    await state.clear()
    await safe_edit_text(callback.message,
        "❌ Тренировка завершена досрочно. Возвращайся скорее! 💪",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("wk:regen:"))
async def regen_workout(callback, state, session):
    data = await state.get_data()
    session_id = data.get("workout_session_id")
    if session_id:
        old_ws = await session.get(WorkoutSession, session_id)
        if old_ws:
            old_ws.status = SessionStatus.skipped
            await session.commit()
    await state.clear()
    await state.set_state(WorkoutStates.choosing_modifier)
    await safe_edit_text(callback.message,
        "🔄 <b>Перегенерируем!</b>\n\nВыбери интенсивность:",
        reply_markup=modifier_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set:replace:"))
async def replace_exercise(callback, state, session, user):
    from models.exercise_alternatives import ExerciseAlternative
    from models.user_equipment import UserEquipment
    from models.exercise import EquipmentCategory
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
    await safe_edit_text(callback.message,
        f"🔄 Замена для <b>{ex.name_ru}</b>\nВыбери альтернативу:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set:do_replace:"))
async def do_replace_exercise(callback, state, session):
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
    await state.update_data(current_reps=None, current_weight=None)
    await safe_edit_text(callback.message,
        f"✅ Заменено на <b>{new_ex.name_ru}</b>\nПодход {cs} из {se.target_sets} · {se.target_reps} повт. · {se.target_weight_kg or 0:.1f} кг",
        reply_markup=set_log_kb(se_id, cs, se.target_reps, se.target_weight_kg or 0.0, exercise_technique_url(new_ex)),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set:cancel_replace:"))
async def cancel_replace(callback, state, session):
    se_id = int(callback.data.split(":")[2])
    se = await session.get(SessionExercise, se_id)
    ex = await session.get(Exercise, se.exercise_id)
    data = await state.get_data()
    cs = data.get("current_set", 1)
    reps = data.get("current_reps") or se.target_reps
    weight = data.get("current_weight") if data.get("current_weight") is not None else (se.target_weight_kg or 0.0)
    weight = float(weight or 0.0)
    await safe_edit_text(callback.message,
        f"<b>{ex.name_ru}</b>\nПодход {cs} из {se.target_sets} · {reps} повт. · {weight:.1f} кг",
        reply_markup=set_log_kb(se_id, cs, reps, weight, exercise_technique_url(ex)),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set:hard:"))
async def set_too_hard(callback, state, session):
    se_id = int(callback.data.split(":")[2])
    se = await session.get(SessionExercise, se_id)
    ex = await session.get(Exercise, se.exercise_id)
    data = await state.get_data()
    cs = data.get("current_set", 1)
    weight = data.get("current_weight") if data.get("current_weight") is not None else (se.target_weight_kg or 0.0)
    weight = float(weight or 0.0)
    reps = int(data.get("current_reps") or se.target_reps or 1)
    step = 2.5 if ex.exercise_type and ex.exercise_type.value == "compound" else 1.25
    new_weight = max(0.0, round(weight - step, 2))
    new_reps = max(1, reps - 1)
    se.target_weight_kg = new_weight
    await state.update_data(current_weight=new_weight, current_reps=new_reps, feedback_rpe=9)
    await session.commit()
    await callback.message.edit_reply_markup(reply_markup=set_log_kb(se_id, cs, new_reps, new_weight, exercise_technique_url(ex)))
    await callback.answer(f"⬇️ Снизил до {new_weight:.1f} кг / {new_reps} повт.")


@router.callback_query(F.data.startswith("set:easy:"))
async def set_too_easy(callback, state, session):
    se_id = int(callback.data.split(":")[2])
    se = await session.get(SessionExercise, se_id)
    ex = await session.get(Exercise, se.exercise_id)
    data = await state.get_data()
    cs = data.get("current_set", 1)
    weight = data.get("current_weight") if data.get("current_weight") is not None else (se.target_weight_kg or 0.0)
    weight = float(weight or 0.0)
    reps = int(data.get("current_reps") or se.target_reps or 1)
    step = 2.5 if ex.exercise_type and ex.exercise_type.value == "compound" else 1.25
    new_weight = round(weight + step, 2)
    new_reps = reps + 1
    se.target_weight_kg = new_weight
    await state.update_data(current_weight=new_weight, current_reps=new_reps, feedback_rpe=6)
    await session.commit()
    await callback.message.edit_reply_markup(reply_markup=set_log_kb(se_id, cs, new_reps, new_weight, exercise_technique_url(ex)))
    await callback.answer(f"⬆️ Поднял до {new_weight:.1f} кг / {new_reps} повт.")


@router.callback_query(F.data == "wk:finish")
async def finish_workout(callback: CallbackQuery, state: FSMContext, user: User, session: AsyncSession):
    data = await state.get_data()
    session_id = data.get("workout_session_id")
    if not session_id:
        await callback.answer("Сессия не найдена.")
        return
    ws = await session.get(WorkoutSession, session_id)
    ws.status = SessionStatus.completed
    ws.completed_at = datetime.utcnow()
    ws.duration_min = int((ws.completed_at - ws.started_at).total_seconds() / 60) if ws.started_at else 45
    vol_res = await session.execute(
        select(func.sum(ExerciseSet.reps_done * ExerciseSet.weight_kg))
        .join(SessionExercise).where(SessionExercise.session_id == session_id)
    )
    total_vol = float(vol_res.scalar() or 0)
    ws.total_volume_kg = total_vol
    ws.calories_burned = calculate_calories_burned(DEFAULT_MET["compound"], 75, ws.duration_min)
    stats_res = await session.execute(select(UserStats).where(UserStats.user_id == user.id))
    stats = stats_res.scalar_one()
    old_level = stats.level
    xp_r = calculate_xp(total_volume_kg=total_vol, difficulty_modifier=ws.difficulty_modifier.value,
                         streak=stats.current_streak, pr_count=0, was_skipped_before=False)
    ws.xp_earned = xp_r.xp_earned
    stats.total_xp += xp_r.xp_earned
    stats.total_workouts += 1
    stats.total_volume_kg = float(stats.total_volume_kg or 0) + total_vol
    stats.level = get_level_from_xp(stats.total_xp)
    stats.last_workout_date = date.today()
    stats.current_streak += 1
    if stats.current_streak > stats.longest_streak:
        stats.longest_streak = stats.current_streak
    await session.commit()

    prs = await detect_prs(session, user.id, session_id)

    # Increment 30-day challenge
    challenge = await session.execute(
        select(UserChallenge).where(UserChallenge.user_id == user.id)
    )
    challenge = challenge.scalar_one_or_none()
    if challenge and not challenge.completed:
        today_str = date.today().isoformat()
        done = set(challenge.workout_days or [])
        done.add(today_str)
        challenge.current_day = len(done)
        challenge.workout_days = list(done)
        if len(done) >= 30:
            challenge.completed = True
            challenge.completed_at = datetime.now()
        await session.commit()

    # Build rich summary with per-exercise comparison
    summary = await build_workout_summary(
        session=session, user_id=user.id, workout_id=session_id,
        xp_earned=xp_r.xp_earned, old_level=old_level,
    )
    summary.prs.extend(prs)
    summary_text = format_summary_message(summary)

    # Plateau + deload notice for next session
    plateau_notices = await check_and_apply_plateau(session, user.id)
    if plateau_notices:
        summary_text += "\n\n" + "\n".join(plateau_notices)

    await callback.message.answer(summary_text, reply_markup=main_menu_keyboard(), parse_mode="HTML")
    await state.clear()


@router.callback_query(F.data.startswith("set:skip:"))
async def skip_exercise(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    se_id = int(callback.data.split(":")[2])
    se = await session.get(SessionExercise, se_id)
    se.is_completed = True
    await session.commit()
    next_res = await session.execute(
        select(SessionExercise).where(SessionExercise.session_id == se.session_id,
                                       SessionExercise.is_completed == False)
        .order_by(asc(SessionExercise.order_index)).limit(1)
    )
    next_se = next_res.scalar_one_or_none()
    await callback.answer("Пропущено")
    await callback.message.edit_reply_markup(reply_markup=exercise_done_kb(next_se.id if next_se else None))
