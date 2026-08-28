"""
Deload-on-return service.

If user had a break of >= BREAK_DAYS_THRESHOLD days since last workout,
reduce target_weight_kg in all planned SessionExercises proportionally.

Break 14-20 days → -15%
Break 21-30 days → -25%
Break > 30 days  → -40%
"""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from models.workout import WorkoutSession, SessionExercise, SessionStatus

BREAK_DAYS_THRESHOLD = 14

DELOAD_FACTORS = [
    (30, 0.60),   # > 30 days → 60% of last weight
    (21, 0.75),   # 21-30 days → 75%
    (14, 0.85),   # 14-20 days → 85%
]


async def apply_return_deload(
    session: AsyncSession,
    user_id: int,
    new_workout_id: int
) -> str | None:
    """
    Called right after a new workout_session is generated.
    Returns a notice string if deload was applied, None otherwise.
    """
    # Find last completed workout date
    res = await session.execute(
        select(WorkoutSession)
        .where(
            WorkoutSession.user_id == user_id,
            WorkoutSession.status == SessionStatus.completed
        )
        .order_by(desc(WorkoutSession.completed_at))
        .limit(1)
    )
    last_ws = res.scalar_one_or_none()
    if not last_ws or not last_ws.completed_at:
        return None

    days_since = (datetime.utcnow() - last_ws.completed_at).days
    if days_since < BREAK_DAYS_THRESHOLD:
        return None

    # Find applicable factor
    factor = None
    for threshold, f in DELOAD_FACTORS:
        if days_since > threshold:
            factor = f
            break
    if factor is None:
        return None

    # Apply to all session_exercises of new workout
    se_res = await session.execute(
        select(SessionExercise)
        .where(SessionExercise.session_id == new_workout_id)
    )
    exercises = se_res.scalars().all()
    for se in exercises:
        if se.target_weight_kg and float(se.target_weight_kg) > 0:
            se.target_weight_kg = round(float(se.target_weight_kg) * factor / 2.5) * 2.5

    await session.commit()
    return (
        f"💪 Добро пожаловать обратно! Ты не тренировался {days_since} дн. "
        f"Веса снижены для плавного входа."
    )
