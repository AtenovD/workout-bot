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
from models.workout import WorkoutSession, SessionExercise, ExerciseSet, SessionStatus, DifficultyModifier, WorkoutReview
from models.gamification import UserStats
from models.challenge import UserChallenge
from models.exercise import Exercise, MuscleGroup
from services.gamification import calculate_xp, get_level_from_xp, get_title
from services.calories import calculate_calories_burned, DEFAULT_MET
from services.pr_detection import detect_prs
from services.plateau_detection import check_and_apply_plateau
from services.deload_on_return import apply_return_deload
from services.rest_timer import run_rest_timer
from services.workout_summary import build_workout_summary, format_summary_message
from services.workout_structure import format_exercise_card, format_workout_overview, warmup_targets_for
from services.training_strategy import format_strategy_note_title
from services.ai_coach import analyze_workout_review
import asyncio
from bot.utils.message_edit import safe_edit_text

router = Router()


def _lang(user: User | None = None) -> str:
    return "en" if user and user.language_code == "en" else "ru"


def modifier_kb(lang: str = "ru"):
    if lang == "en":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🟢 Light", callback_data="mod:light")],
            [InlineKeyboardButton(text="⚪ Normal", callback_data="mod:normal")],
            [InlineKeyboardButton(text="🔴 Heavy", callback_data="mod:hard")],
        ])

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Облегчённый", callback_data="mod:light")],
        [InlineKeyboardButton(text="⚪ Обычный", callback_data="mod:normal")],
        [InlineKeyboardButton(text="🔴 Утяжелённый", callback_data="mod:hard")],
    ])


def workout_start_text(lang: str = "ru") -> str:
    if lang == "en":
        return "🏋️ <b>Starting your workout!</b>\n\nHow do you feel today?"
    return "🏋️ <b>Начинаем тренировку!</b>\n\nКак себя чувствуешь сегодня?"


def active_workout_text(lang: str = "ru") -> str:
    if lang == "en":
        return "You have an unfinished workout. Continue?"
    return "У тебя есть незавершённая тренировка. Продолжить?"


def regen_text(lang: str = "ru") -> str:
    if lang == "en":
        return "🔄 <b>Regenerating workout!</b>\n\nChoose intensity:"
    return "🔄 <b>Перегенерируем!</b>\n\nВыбери интенсивность:"

def overview_kb(session_id, lang: str = "ru"):
    if lang == "en":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Start", callback_data=f"wk:begin:{session_id}")],
            [InlineKeyboardButton(text="🔄 Regenerate", callback_data=f"wk:regen:{session_id}")],
            [InlineKeyboardButton(text="◀️ Back", callback_data="menu:back")],
        ])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Начать", callback_data=f"wk:begin:{session_id}")],
        [InlineKeyboardButton(text="🔄 Перегенерировать", callback_data=f"wk:regen:{session_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:back")],
    ])

def set_log_kb(se_id, set_num, reps, weight, technique_url=None, is_warmup=False, lang: str = "ru"):
    if lang == "en":
        done_text = f"✅ Warm-up {set_num} done" if is_warmup else f"✅ Set {set_num} done"
        reps_text = "reps"
        hard_text = "😰 Hard"
        easy_text = "😊 Easy"
        replace_text = "🔄 Replace"
        skip_text = "⏭ Skip"
        technique_text = "🎞 Technique"
    else:
        done_text = f"✅ Разминка {set_num} — готово" if is_warmup else f"✅ Подход {set_num} — выполнен!"
        reps_text = "повт."
        hard_text = "😰 Тяжело"
        easy_text = "😊 Легко"
        replace_text = "🔄 Заменить"
        skip_text = "⏭ Пропустить"
        technique_text = "🎞 Техника"
    rows = [
        [InlineKeyboardButton(text="−", callback_data=f"set:rm:{se_id}"),
         InlineKeyboardButton(text=f"🔁 {reps} {reps_text}", callback_data=f"set:rs:{se_id}"),
         InlineKeyboardButton(text="+", callback_data=f"set:rp:{se_id}")],
        [InlineKeyboardButton(text="−2.5", callback_data=f"set:wm:{se_id}"),
         InlineKeyboardButton(text=f"⚖️ {float(weight):.1f} {'kg' if lang == 'en' else 'кг'}", callback_data=f"set:ws:{se_id}"),
         InlineKeyboardButton(text="+2.5", callback_data=f"set:wp:{se_id}")],
        [InlineKeyboardButton(text=done_text, callback_data=f"set:done:{se_id}")],
        [InlineKeyboardButton(text=hard_text, callback_data=f"set:hard:{se_id}"),
         InlineKeyboardButton(text=easy_text, callback_data=f"set:easy:{se_id}")],
        [InlineKeyboardButton(text=replace_text, callback_data=f"set:replace:{se_id}"),
         InlineKeyboardButton(text=skip_text, callback_data=f"set:skip:{se_id}")],
    ]
    if technique_url:
        rows.append([InlineKeyboardButton(text=technique_text, url=technique_url)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def exercise_technique_url(ex):
    return getattr(ex, "gif_url", None) or getattr(ex, "photo_url", None) or getattr(ex, "video_url", None)


async def send_exercise_card(
    message: Message,
    text: str,
    reply_markup: InlineKeyboardMarkup,
    ex: Exercise,
    *,
    edit_text: bool = False,
):
    if getattr(ex, "gif_url", None):
        try:
            await message.answer_animation(
                ex.gif_url,
                caption=text,
                reply_markup=reply_markup,
                parse_mode="HTML",
            )
            return
        except Exception:
            pass
    if getattr(ex, "photo_url", None):
        try:
            await message.answer_photo(
                ex.photo_url,
                caption=text,
                reply_markup=reply_markup,
                parse_mode="HTML",
            )
            return
        except Exception:
            pass
    if edit_text:
        await safe_edit_text(message, text, reply_markup=reply_markup, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")


async def _muscle_names_by_id(session: AsyncSession, lang: str = "ru") -> dict[int, str]:
    column = MuscleGroup.name_en if lang == "en" else MuscleGroup.name_ru
    result = await session.execute(select(MuscleGroup.id, column))
    return {mg_id: name for mg_id, name in result.all()}


def _current_warmup_target(se, ex, modifier, warmup_index):
    targets = warmup_targets_for(se, ex, modifier)
    if not targets:
        return None
    index = min(max(int(warmup_index or 1), 1), len(targets)) - 1
    return targets[index]


def _default_set_values(se, ex, modifier, phase, warmup_index):
    if phase == "warmup":
        target = _current_warmup_target(se, ex, modifier, warmup_index)
        if target:
            return target.reps, target.weight_kg
    return se.target_reps, float(se.target_weight_kg or 0.0)

def rest_kb(se_id, next_set, lang: str = "ru"):
    if lang == "en":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💪 Next set", callback_data=f"rest:next:{se_id}:{next_set}")],
            [InlineKeyboardButton(text="⏭ Skip rest", callback_data=f"rest:skip:{se_id}:{next_set}")],
        ])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💪 Следующий подход", callback_data=f"rest:next:{se_id}:{next_set}")],
        [InlineKeyboardButton(text="⏭ Пропустить отдых", callback_data=f"rest:skip:{se_id}:{next_set}")],
    ])

def exercise_done_kb(next_se_id, lang: str = "ru"):
    if next_se_id:
        text = "➡️ Next exercise" if lang == "en" else "➡️ Следующее упражнение"
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=f"ex:next:{next_se_id}")]])
    text = "🏁 Finish workout" if lang == "en" else "🏁 Завершить тренировку"
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, callback_data="wk:finish")]])


def review_intensity_kb(session_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Хочу сложнее", callback_data=f"review:intensity:{session_id}:harder")],
        [InlineKeyboardButton(text="✅ Нормально", callback_data=f"review:intensity:{session_id}:ok")],
        [InlineKeyboardButton(text="🧊 Нужно легче", callback_data=f"review:intensity:{session_id}:easier")],
    ])


def review_pain_kb(session_id: int, intensity: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ничего не болит", callback_data=f"review:pain:{session_id}:{intensity}:none")],
        [InlineKeyboardButton(text="⚠️ Есть дискомфорт", callback_data=f"review:pain:{session_id}:{intensity}:discomfort")],
        [InlineKeyboardButton(text="🛑 Есть боль", callback_data=f"review:pain:{session_id}:{intensity}:pain")],
    ])


async def _skipped_exercises(session: AsyncSession, session_id: int):
    result = await session.execute(
        select(SessionExercise, Exercise)
        .join(Exercise, SessionExercise.exercise_id == Exercise.id)
        .where(SessionExercise.session_id == session_id, SessionExercise.was_skipped == True)
        .order_by(asc(SessionExercise.order_index))
    )
    return result.all()


@router.message(Command("workout"))
@router.message(F.text.in_({"🏋️ Тренировка", "🏋️ Workout"}))
@router.callback_query(F.data == "menu:workout")
async def start_workout(event, state: FSMContext, user: User, session: AsyncSession, **kwargs):
    lang = _lang(user)
    msg = event.message if isinstance(event, CallbackQuery) else event
    existing = await session.execute(
        select(WorkoutSession).where(WorkoutSession.user_id == user.id,
                                     WorkoutSession.status == SessionStatus.in_progress).limit(1)
    )
    active = existing.scalar_one_or_none()
    if active:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Continue" if lang == "en" else "▶️ Продолжить", callback_data=f"wk:resume:{active.id}")],
            [InlineKeyboardButton(text="❌ End now" if lang == "en" else "❌ Завершить досрочно", callback_data=f"wk:abort:{active.id}")],
        ])
        await msg.answer(active_workout_text(lang), reply_markup=kb)
        return
    await state.set_state(WorkoutStates.choosing_modifier)
    await state.update_data(language=lang)
    await send_module_visual(event, "workout", workout_start_text(lang), reply_markup=modifier_kb(lang))


@router.callback_query(F.data.startswith("mod:"))
async def choose_modifier(callback: CallbackQuery, state: FSMContext, user: User, session: AsyncSession):
    lang = _lang(user)
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
    total_time = sum(se.target_sets * (45 + se.rest_seconds) for se, _ in exercises) // 60 + 10
    muscle_names = await _muscle_names_by_id(session, lang)
    strategy_title = format_strategy_note_title(ws.notes, lang=lang)
    await state.update_data(workout_session_id=ws.id, language=lang)
    await state.set_state(WorkoutStates.overview)
    await safe_edit_text(callback.message,
        format_workout_overview(
            exercises,
            modifier,
            profile.goal,
            total_time,
            profile.training_structure,
            profile.split_type,
            muscle_names,
            strategy_title,
            lang=lang,
        ),
        reply_markup=overview_kb(ws.id, lang), parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("wk:begin:"))
async def begin_workout(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("language", "ru")
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
    modifier = ws.difficulty_modifier.value
    warmups = warmup_targets_for(first_se, ex, modifier)
    phase = "warmup" if warmups else "work"
    reps = warmups[0].reps if warmups else first_se.target_reps
    weight = warmups[0].weight_kg if warmups else float(first_se.target_weight_kg or 0.0)
    await state.update_data(
        current_set=1,
        warmup_index=1,
        set_phase=phase,
        current_reps=None,
        current_weight=None,
        workout_modifier=modifier,
        language=lang,
    )
    await state.set_state(WorkoutStates.logging_set)

    muscle_names = await _muscle_names_by_id(session, lang)
    await send_exercise_card(
        callback.message,
        format_exercise_card(first_se, ex, 1, modifier, is_warmup=phase == "warmup", warmup_index=1, muscle_names_by_id=muscle_names, lang=lang),
        reply_markup=set_log_kb(first_se.id, 1, reps, weight, exercise_technique_url(ex), is_warmup=phase == "warmup", lang=lang),
        ex=ex,
        edit_text=True,
    )


@router.callback_query(F.data.startswith("set:done:"))
async def set_done(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    se_id = int(callback.data.split(":")[2])
    data = await state.get_data()
    lang = data.get("language", "ru")
    se = await session.get(SessionExercise, se_id)
    ex = await session.get(Exercise, se.exercise_id)
    modifier = data.get("workout_modifier", "normal")
    phase = data.get("set_phase", "work")
    warmup_index = int(data.get("warmup_index") or 1)
    current_set = data.get("current_set", 1)
    default_reps, default_weight = _default_set_values(se, ex, modifier, phase, warmup_index)
    reps = data.get("current_reps") or default_reps
    weight = data.get("current_weight") if data.get("current_weight") is not None else default_weight

    if phase == "warmup":
        session.add(ExerciseSet(
            session_exercise_id=se_id,
            set_number=warmup_index,
            reps_done=reps,
            weight_kg=weight,
            rpe=data.get("feedback_rpe"),
            is_warmup=True,
        ))
        await session.commit()

        warmups = warmup_targets_for(se, ex, modifier)
        if warmup_index < len(warmups):
            next_index = warmup_index + 1
            next_target = warmups[next_index - 1]
            muscle_names = await _muscle_names_by_id(session, lang)
            await state.update_data(warmup_index=next_index, current_reps=None, current_weight=None, feedback_rpe=None)
            await safe_edit_text(
                callback.message,
                format_exercise_card(se, ex, 1, modifier, is_warmup=True, warmup_index=next_index, muscle_names_by_id=muscle_names, lang=lang),
                reply_markup=set_log_kb(
                    se_id, next_index, next_target.reps, next_target.weight_kg,
                    exercise_technique_url(ex), is_warmup=True, lang=lang,
                ),
                parse_mode="HTML",
            )
            await callback.answer(f"✅ Warm-up {warmup_index} logged." if lang == "en" else f"✅ Разминка {warmup_index} засчитана.")
            return

        muscle_names = await _muscle_names_by_id(session, lang)
        await state.update_data(set_phase="work", current_set=1, current_reps=None, current_weight=None, feedback_rpe=None)
        await safe_edit_text(
            callback.message,
            format_exercise_card(se, ex, 1, modifier, muscle_names_by_id=muscle_names, lang=lang),
            reply_markup=set_log_kb(se_id, 1, se.target_reps, se.target_weight_kg or 0.0, exercise_technique_url(ex), lang=lang),
            parse_mode="HTML",
        )
        await callback.answer("✅ Warm-up done. Moving to working sets." if lang == "en" else "✅ Разминка готова. Переходим к рабочим подходам.")
        return

    session.add(ExerciseSet(
        session_exercise_id=se_id,
        set_number=current_set,
        reps_done=reps,
        weight_kg=weight,
        rpe=data.get("feedback_rpe"),
    ))
    if current_set >= se.target_sets:
        se.is_completed = True
        await session.commit()
        next_res = await session.execute(
            select(SessionExercise).where(SessionExercise.session_id == se.session_id,
                                           SessionExercise.is_completed == False)
            .order_by(asc(SessionExercise.order_index)).limit(1)
        )
        next_se = next_res.scalar_one_or_none()
        await state.update_data(current_set=1, warmup_index=1, set_phase="work", current_reps=None, current_weight=None, feedback_rpe=None)
        await callback.message.edit_reply_markup(reply_markup=exercise_done_kb(next_se.id if next_se else None, lang))
        await callback.answer("✅ Exercise complete!" if lang == "en" else "✅ Упражнение выполнено!")
    else:
        await session.commit()
        next_set = current_set + 1
        await state.update_data(current_set=next_set, current_reps=None, current_weight=None, feedback_rpe=None)
        asyncio.create_task(run_rest_timer(callback.bot, callback.message.chat.id, se_id, next_set, se.rest_seconds or 90))
        await callback.message.edit_reply_markup(reply_markup=rest_kb(se_id, next_set, lang))
        await callback.answer(
            f"✅ Set {current_set} logged! Rest {se.rest_seconds or 90} sec."
            if lang == "en"
            else f"✅ Подход {current_set} засчитан! Отдыхай {se.rest_seconds or 90} сек."
        )


@router.callback_query(F.data.startswith("set:rm:") | F.data.startswith("set:rp:") |
                        F.data.startswith("set:wm:") | F.data.startswith("set:wp:"))
async def adjust_values(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    parts = callback.data.split(":")
    action, se_id = parts[1], int(parts[2])
    se = await session.get(SessionExercise, se_id)
    data = await state.get_data()
    lang = data.get("language", "ru")
    ex = await session.get(Exercise, se.exercise_id)
    modifier = data.get("workout_modifier", "normal")
    phase = data.get("set_phase", "work")
    warmup_index = int(data.get("warmup_index") or 1)
    current_set = data.get("current_set", 1)
    visible_set = warmup_index if phase == "warmup" else current_set
    default_reps, default_weight = _default_set_values(se, ex, modifier, phase, warmup_index)
    reps = int(data.get("current_reps") or default_reps or 1)
    weight = data.get("current_weight") if data.get("current_weight") is not None else default_weight
    weight = float(weight or 0.0)
    if action == "rm": reps = max(1, reps - 1)
    elif action == "rp": reps = reps + 1
    elif action == "wm": weight = max(0.0, round(weight - 2.5, 2))
    elif action == "wp": weight = round(weight + 2.5, 2)
    await state.update_data(current_reps=reps, current_weight=weight)
    await callback.message.edit_reply_markup(reply_markup=set_log_kb(
        se_id, visible_set, reps, weight, exercise_technique_url(ex), is_warmup=phase == "warmup", lang=lang,
    ))
    await callback.answer()


@router.callback_query(F.data.startswith("set:rs:") | F.data.startswith("set:ws:"))
async def set_display_value(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "ru")
    await callback.answer("Use − / + near the value." if lang == "en" else "Используй − / + рядом с показателем.")


@router.callback_query(F.data.startswith("rest:"))
async def rest_done(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    parts = callback.data.split(":")
    se_id, next_set = int(parts[2]), int(parts[3])
    se = await session.get(SessionExercise, se_id)
    ex = await session.get(Exercise, se.exercise_id)
    await state.update_data(current_set=next_set, set_phase="work")
    data = await state.get_data()
    lang = data.get("language", "ru")
    modifier = data.get("workout_modifier", "normal")
    muscle_names = await _muscle_names_by_id(session, lang)
    await safe_edit_text(callback.message,
        format_exercise_card(se, ex, next_set, modifier, muscle_names_by_id=muscle_names, lang=lang),
        reply_markup=set_log_kb(se_id, next_set, se.target_reps, se.target_weight_kg or 0.0, exercise_technique_url(ex), lang=lang),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("ex:next:"))
async def next_exercise(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    se_id = int(callback.data.split(":")[2])
    se = await session.get(SessionExercise, se_id)
    ex = await session.get(Exercise, se.exercise_id)
    data = await state.get_data()
    lang = data.get("language", "ru")
    modifier = data.get("workout_modifier", "normal")
    warmups = warmup_targets_for(se, ex, modifier)
    phase = "warmup" if warmups else "work"
    reps = warmups[0].reps if warmups else se.target_reps
    weight = warmups[0].weight_kg if warmups else float(se.target_weight_kg or 0.0)
    await state.update_data(
        current_set=1,
        warmup_index=1,
        set_phase=phase,
        current_reps=None,
        current_weight=None,
    )
    muscle_names = await _muscle_names_by_id(session, lang)
    await send_exercise_card(
        callback.message,
        format_exercise_card(se, ex, 1, modifier, is_warmup=phase == "warmup", warmup_index=1, muscle_names_by_id=muscle_names, lang=lang),
        reply_markup=set_log_kb(se_id, 1, reps, weight, exercise_technique_url(ex), is_warmup=phase == "warmup", lang=lang),
        ex=ex,
    )



@router.callback_query(F.data.startswith("wk:resume:"))
async def resume_workout(callback, state, session, user: User):
    lang = _lang(user)
    session_id = int(callback.data.split(":")[2])
    ws = await session.get(WorkoutSession, session_id)
    if not ws:
        await callback.answer("Сессия не найдена.")
        return
    ws.status = SessionStatus.in_progress
    await session.commit()
    await state.update_data(workout_session_id=session_id, workout_modifier=ws.difficulty_modifier.value, language=lang)
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
    modifier = ws.difficulty_modifier.value
    warmups = warmup_targets_for(se, ex, modifier)
    phase = "warmup" if warmups else "work"
    reps = warmups[0].reps if warmups else se.target_reps
    weight = warmups[0].weight_kg if warmups else float(se.target_weight_kg or 0.0)
    await state.update_data(
        current_set=1,
        warmup_index=1,
        set_phase=phase,
        current_reps=None,
        current_weight=None,
    )
    muscle_names = await _muscle_names_by_id(session, lang)
    await send_exercise_card(
        callback.message,
        "▶️ " + format_exercise_card(se, ex, 1, modifier, is_warmup=phase == "warmup", warmup_index=1, muscle_names_by_id=muscle_names, lang=lang),
        reply_markup=set_log_kb(se.id, 1, reps, weight, exercise_technique_url(ex), is_warmup=phase == "warmup", lang=lang),
        ex=ex,
        edit_text=True,
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
async def regen_workout(callback, state, session, user: User):
    lang = _lang(user)
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
        regen_text(lang),
        reply_markup=modifier_kb(lang),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set:replace:"))
async def replace_exercise(callback, state, session, user):
    lang = _lang(user)
    from models.exercise_alternatives import ExerciseAlternative
    from models.user_equipment import UserEquipment
    from models.exercise import EquipmentCategory
    se_id = int(callback.data.split(":")[2])
    se = await session.get(SessionExercise, se_id)
    if not se:
        await callback.answer("Exercise not found." if lang == "en" else "Упражнение не найдено.")
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
            alt_name = alt_ex.name_en if lang == "en" else alt_ex.name_ru
            buttons.append([InlineKeyboardButton(text=f"🔄 {alt_name}", callback_data=f"set:do_replace:{se_id}:{alt_ex.id}")])
    if not buttons:
        await callback.answer(
            "No available replacements with your equipment." if lang == "en" else "Нет доступных замен с твоим инвентарём.",
            show_alert=True,
        )
        return
    buttons.append([InlineKeyboardButton(text="❌ Cancel" if lang == "en" else "❌ Отмена", callback_data=f"set:cancel_replace:{se_id}")])
    ex_name = ex.name_en if lang == "en" else ex.name_ru
    text = (
        f"🔄 Replacement for <b>{ex_name}</b>\nChoose an alternative:"
        if lang == "en"
        else f"🔄 Замена для <b>{ex_name}</b>\nВыбери альтернативу:"
    )
    await safe_edit_text(callback.message,
        text,
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
    data = await state.get_data()
    lang = data.get("language", "ru")
    if not se or not new_ex:
        await callback.answer("Replacement error." if lang == "en" else "Ошибка замены.")
        return
    se.exercise_id = new_ex_id
    await session.commit()
    cs = data.get("current_set", 1)
    modifier = data.get("workout_modifier", "normal")
    phase = data.get("set_phase", "work")
    warmup_index = int(data.get("warmup_index") or 1)
    if phase == "warmup" and not warmup_targets_for(se, new_ex, modifier):
        phase = "work"
        await state.update_data(set_phase="work", current_set=1, warmup_index=1)
        cs = 1
    visible_set = warmup_index if phase == "warmup" else cs
    reps, weight = _default_set_values(se, new_ex, modifier, phase, warmup_index)
    await state.update_data(current_reps=None, current_weight=None)
    muscle_names = await _muscle_names_by_id(session, lang)
    prefix = "✅ Replaced\n" if lang == "en" else "✅ Заменено\n"
    await send_exercise_card(
        callback.message,
        prefix + format_exercise_card(
            se, new_ex, cs, modifier, is_warmup=phase == "warmup", warmup_index=warmup_index, muscle_names_by_id=muscle_names, lang=lang,
        ),
        reply_markup=set_log_kb(
            se_id, visible_set, reps, weight, exercise_technique_url(new_ex), is_warmup=phase == "warmup", lang=lang,
        ),
        ex=new_ex,
        edit_text=True,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set:cancel_replace:"))
async def cancel_replace(callback, state, session):
    se_id = int(callback.data.split(":")[2])
    se = await session.get(SessionExercise, se_id)
    ex = await session.get(Exercise, se.exercise_id)
    data = await state.get_data()
    lang = data.get("language", "ru")
    cs = data.get("current_set", 1)
    modifier = data.get("workout_modifier", "normal")
    phase = data.get("set_phase", "work")
    warmup_index = int(data.get("warmup_index") or 1)
    visible_set = warmup_index if phase == "warmup" else cs
    default_reps, default_weight = _default_set_values(se, ex, modifier, phase, warmup_index)
    reps = data.get("current_reps") or default_reps
    weight = data.get("current_weight") if data.get("current_weight") is not None else default_weight
    weight = float(weight or 0.0)
    muscle_names = await _muscle_names_by_id(session, lang)
    await safe_edit_text(callback.message,
        format_exercise_card(se, ex, cs, modifier, is_warmup=phase == "warmup", warmup_index=warmup_index, muscle_names_by_id=muscle_names, lang=lang),
        reply_markup=set_log_kb(se_id, visible_set, reps, weight, exercise_technique_url(ex), is_warmup=phase == "warmup", lang=lang),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set:hard:"))
async def set_too_hard(callback, state, session):
    se_id = int(callback.data.split(":")[2])
    se = await session.get(SessionExercise, se_id)
    ex = await session.get(Exercise, se.exercise_id)
    data = await state.get_data()
    lang = data.get("language", "ru")
    cs = data.get("current_set", 1)
    modifier = data.get("workout_modifier", "normal")
    phase = data.get("set_phase", "work")
    warmup_index = int(data.get("warmup_index") or 1)
    visible_set = warmup_index if phase == "warmup" else cs
    default_reps, default_weight = _default_set_values(se, ex, modifier, phase, warmup_index)
    weight = data.get("current_weight") if data.get("current_weight") is not None else default_weight
    weight = float(weight or 0.0)
    reps = int(data.get("current_reps") or default_reps or 1)
    step = 2.5 if ex.exercise_type and ex.exercise_type.value == "compound" else 1.25
    new_weight = max(0.0, round(weight - step, 2))
    new_reps = max(1, reps - 1)
    if phase != "warmup":
        se.target_weight_kg = new_weight
    await state.update_data(current_weight=new_weight, current_reps=new_reps, feedback_rpe=9)
    await session.commit()
    await callback.message.edit_reply_markup(reply_markup=set_log_kb(
        se_id, visible_set, new_reps, new_weight, exercise_technique_url(ex), is_warmup=phase == "warmup", lang=lang,
    ))
    await callback.answer(
        f"⬇️ Lowered to {new_weight:.1f} kg / {new_reps} reps."
        if lang == "en"
        else f"⬇️ Снизил до {new_weight:.1f} кг / {new_reps} повт."
    )


@router.callback_query(F.data.startswith("set:easy:"))
async def set_too_easy(callback, state, session):
    se_id = int(callback.data.split(":")[2])
    se = await session.get(SessionExercise, se_id)
    ex = await session.get(Exercise, se.exercise_id)
    data = await state.get_data()
    lang = data.get("language", "ru")
    cs = data.get("current_set", 1)
    modifier = data.get("workout_modifier", "normal")
    phase = data.get("set_phase", "work")
    warmup_index = int(data.get("warmup_index") or 1)
    visible_set = warmup_index if phase == "warmup" else cs
    default_reps, default_weight = _default_set_values(se, ex, modifier, phase, warmup_index)
    weight = data.get("current_weight") if data.get("current_weight") is not None else default_weight
    weight = float(weight or 0.0)
    reps = int(data.get("current_reps") or default_reps or 1)
    step = 2.5 if ex.exercise_type and ex.exercise_type.value == "compound" else 1.25
    new_weight = round(weight + step, 2)
    new_reps = reps + 1
    if phase != "warmup":
        se.target_weight_kg = new_weight
    await state.update_data(current_weight=new_weight, current_reps=new_reps, feedback_rpe=6)
    await session.commit()
    await callback.message.edit_reply_markup(reply_markup=set_log_kb(
        se_id, visible_set, new_reps, new_weight, exercise_technique_url(ex), is_warmup=phase == "warmup", lang=lang,
    ))
    await callback.answer(
        f"⬆️ Raised to {new_weight:.1f} kg / {new_reps} reps."
        if lang == "en"
        else f"⬆️ Поднял до {new_weight:.1f} кг / {new_reps} повт."
    )


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
        .join(SessionExercise).where(
            SessionExercise.session_id == session_id,
            ExerciseSet.is_warmup == False,
        )
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

    await callback.message.answer(summary_text, reply_markup=main_menu_keyboard(telegram_id=user.telegram_id), parse_mode="HTML")
    skipped = await _skipped_exercises(session, session_id)
    skipped_text = "скипов не было" if not skipped else "скипнул: " + ", ".join(ex.name_ru for _, ex in skipped)
    await callback.message.answer(
        "🧠 <b>Короткое ревью</b>\n"
        f"Я вижу, что {skipped_text}.\n\n"
        "Как ощущалась нагрузка? Это пойдёт в расчёт следующей тренировки.",
        reply_markup=review_intensity_kb(session_id),
        parse_mode="HTML",
    )
    await state.clear()


@router.callback_query(F.data.startswith("set:skip:"))
async def skip_exercise(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("language", "ru")
    se_id = int(callback.data.split(":")[2])
    se = await session.get(SessionExercise, se_id)
    se.is_completed = True
    se.was_skipped = True
    await session.commit()
    next_res = await session.execute(
        select(SessionExercise).where(SessionExercise.session_id == se.session_id,
                                       SessionExercise.is_completed == False)
        .order_by(asc(SessionExercise.order_index)).limit(1)
    )
    next_se = next_res.scalar_one_or_none()
    await callback.answer("Skipped" if lang == "en" else "Пропущено")
    await callback.message.edit_reply_markup(reply_markup=exercise_done_kb(next_se.id if next_se else None, lang))


@router.callback_query(F.data.startswith("review:intensity:"))
async def review_intensity(callback: CallbackQuery):
    _, _, session_id, intensity = callback.data.split(":")
    labels = {
        "harder": "Хочешь сложнее — понял.",
        "ok": "Нагрузка нормальная — отлично.",
        "easier": "Нужно легче — учту.",
    }
    await safe_edit_text(
        callback.message,
        "🧠 <b>Короткое ревью</b>\n"
        f"{labels.get(intensity, 'Нагрузку учту')}\n\n"
        "По самочувствию: есть боль или неприятный дискомфорт?",
        reply_markup=review_pain_kb(int(session_id), intensity),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("review:pain:"))
async def review_pain(callback: CallbackQuery, user: User, session: AsyncSession):
    _, _, session_id, intensity, pain = callback.data.split(":")
    session_id = int(session_id)
    skipped = await _skipped_exercises(session, session_id)
    skipped_ids = [se.exercise_id for se, _ in skipped]
    skipped_names = [ex.name_ru for _, ex in skipped]

    ws = await session.get(WorkoutSession, session_id)
    if ws:
        ws.rpe_session = {"harder": 6, "ok": 8, "easier": 9}.get(intensity)

    review = WorkoutReview(
        workout_session_id=session_id,
        user_id=user.id,
        intensity_feedback=intensity,
        pain_feedback=pain,
        skipped_exercise_ids=skipped_ids,
        skipped_exercise_names=skipped_names,
    )
    session.add(review)
    await session.flush()
    await session.commit()

    ai_result = await analyze_workout_review(session, user.id, session_id, review)
    review.ai_adjustment = ai_result.adjustment
    review.ai_coach_note = ai_result.coach_note
    review.ai_model = ai_result.model
    review.ai_error = ai_result.error
    await session.commit()

    pain_text = {
        "none": "Без боли — можно продолжать прогрессию.",
        "discomfort": "Дискомфорт записал, следующую тренировку сделаю осторожнее.",
        "pain": "Боль записал, следующую тренировку заметно разгружу.",
    }.get(pain, "Самочувствие записал.")
    ai_note = f"\n\n🤖 {ai_result.coach_note}" if ai_result.coach_note else ""
    await safe_edit_text(
        callback.message,
        "✅ <b>Ревью сохранено</b>\n"
        f"{pain_text}\n"
        "На следующей тренировке бот учтёт нагрузку, скипы и самочувствие."
        f"{ai_note}",
        reply_markup=main_menu_keyboard(telegram_id=user.telegram_id),
        parse_mode="HTML",
    )
    await callback.answer("Сохранено")
