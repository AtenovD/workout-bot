"""
Plateau detection + auto-deload.

Plateau: no weight increase across last N_SESSIONS completed workouts for same exercise.
Deload:  if plateau detected → reduce target_weight_kg of upcoming planned exercises by 10%.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from models.workout import WorkoutSession, SessionExercise, ExerciseSet, SessionStatus
from models.exercise import Exercise

N_SESSIONS = 3
DELOAD_FACTOR = 0.90
MIN_HISTORY = 4


async def check_and_apply_plateau(session: AsyncSession, user_id: int) -> list[str]:
    """Returns deload notices applied (empty list if nothing triggered)."""
    res = await session.execute(
        select(WorkoutSession)
        .where(WorkoutSession.user_id == user_id, WorkoutSession.status == SessionStatus.completed)
        .order_by(desc(WorkoutSession.finished_at))
        .limit(N_SESSIONS + 1)
    )
    recent = res.scalars().all()
    if len(recent) < MIN_HISTORY:
        return []

    ex_history: dict[int, list[float]] = {}
    ex_names: dict[int, str] = {}

    for ws in recent:
        rows = await session.execute(
            select(SessionExercise, Exercise)
            .join(Exercise, SessionExercise.exercise_id == Exercise.id)
            .where(SessionExercise.session_id == ws.id, SessionExercise.is_completed == True)
        )
        for se, ex in rows.all():
            sets_res = await session.execute(
                select(ExerciseSet).where(ExerciseSet.session_exercise_id == se.id)
            )
            sets = sets_res.scalars().all()
            if not sets:
                continue
            max_w = max((float(s.weight_kg or 0) for s in sets), default=0.0)
            ex_history.setdefault(ex.id, []).append(max_w)
            ex_names[ex.id] = getattr(ex, 'name_ru', ex.name)

    notices = []
    for eid, weights in ex_history.items():
        if len(weights) < N_SESSIONS:
            continue
        if not all(weights[i] <= weights[i + 1] for i in range(len(weights) - 1)):
            continue
        upcoming_res = await session.execute(
            select(SessionExercise)
            .join(WorkoutSession, SessionExercise.session_id == WorkoutSession.id)
            .where(
                WorkoutSession.user_id == user_id,
                WorkoutSession.status == SessionStatus.planned,
                SessionExercise.exercise_id == eid,
            )
        )
        upcoming = upcoming_res.scalars().all()
        if not upcoming:
            continue
        current_w = weights[0]
        new_w = round(current_w * DELOAD_FACTOR, 1)
        for se in upcoming:
            se.target_weight_kg = new_w
        await session.commit()
        notices.append(
            f"\U0001f4c9 <b>\u0414\u0438\u043b\u043e\u0430\u0434</b> {ex_names[eid]}: {current_w:.1f} \u2192 {new_w:.1f} \u043a\u0433 "
            f"(\u043d\u0435\u0442 \u043f\u0440\u043e\u0433\u0440\u0435\u0441\u0441\u0430 {N_SESSIONS} \u0442\u0440\u0435\u043d\u0438\u0440\u043e\u0432\u043e\u043a)"
        )
    return notices
