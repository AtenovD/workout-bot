"""
Achievement checker — checks and unlocks achievements after each workout.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from models.user import User
from models.workout import WorkoutSession, SessionStatus, ExerciseSet, SessionExercise
from models.gamification import Achievement, UserAchievement, UserStats
from models.profile import Profile
from models.personal_record import PersonalRecord


async def check_and_unlock(
    session: AsyncSession,
    user: User,
    stats: UserStats,
    workout: WorkoutSession,
) -> list[Achievement]:
    """Check all achievements and unlock new ones. Returns list of newly unlocked."""
    # Load all achievements
    all_ach = list((await session.execute(select(Achievement))).scalars())
    # Already unlocked
    unlocked_ids = {ua.achievement_id for ua in (await session.execute(
        select(UserAchievement).where(UserAchievement.user_id == user.id)
    )).scalars()}

    # Extra stats
    pr_count_res = await session.execute(
        select(func.count()).select_from(PersonalRecord).where(PersonalRecord.user_id == user.id)
    )
    pr_count = pr_count_res.scalar() or 0

    profile_res = await session.execute(select(Profile).where(Profile.user_id == user.id))
    profile = profile_res.scalar_one_or_none()
    body_weight = float(profile.current_weight_kg or 80) if profile else 80.0

    newly_unlocked = []

    for ach in all_ach:
        if ach.id in unlocked_ids:
            continue

        cond = ach.condition
        ctype = cond.get("type")
        unlocked = False

        if ctype == "total_workouts":
            unlocked = stats.total_workouts >= cond["value"]
        elif ctype == "streak":
            unlocked = stats.current_streak >= cond["value"]
        elif ctype == "pr_count":
            unlocked = pr_count >= cond["value"]
        elif ctype == "level":
            unlocked = stats.level >= cond["value"]
        elif ctype == "session_volume":
            unlocked = float(workout.total_volume_kg or 0) >= cond["value"]
        elif ctype == "total_volume":
            unlocked = float(stats.total_volume_kg or 0) >= cond["value"]
        elif ctype == "hard_sessions":
            hard_res = await session.execute(
                select(func.count()).select_from(WorkoutSession).where(
                    WorkoutSession.user_id == user.id,
                    WorkoutSession.difficulty_modifier == "hard",
                    WorkoutSession.status == SessionStatus.completed,
                )
            )
            unlocked = (hard_res.scalar() or 0) >= cond["value"]
        elif ctype == "exercise_ratio":
            ex_code = cond.get("exercise")
            ratio = cond.get("ratio", 1.0)
            pr_res = await session.execute(
                select(PersonalRecord.value).join(
                    SessionExercise, PersonalRecord.exercise_id == SessionExercise.exercise_id
                ).limit(1)
            )
            pr_val = pr_res.scalar_one_or_none()
            if pr_val:
                unlocked = float(pr_val) >= body_weight * ratio
        elif ctype == "workout_before_hour":
            if workout.started_at:
                unlocked = workout.started_at.hour < cond["value"]
        elif ctype == "workout_after_hour":
            if workout.started_at:
                unlocked = workout.started_at.hour >= cond["value"]
        elif ctype == "return_after_days":
            if stats.last_workout_date and stats.current_streak == 1:
                from sqlalchemy import desc as sdesc
                prev_res = await session.execute(
                    select(WorkoutSession).where(
                        WorkoutSession.user_id == user.id,
                        WorkoutSession.status == SessionStatus.completed,
                    ).order_by(sdesc(WorkoutSession.completed_at)).offset(1).limit(1)
                )
                prev = prev_res.scalar_one_or_none()
                if prev and prev.completed_at:
                    gap = (workout.completed_at - prev.completed_at).days
                    unlocked = gap >= cond["value"]

        if unlocked:
            session.add(UserAchievement(user_id=user.id, achievement_id=ach.id, progress=1.0))
            stats.total_xp += ach.xp_reward
            newly_unlocked.append(ach)

    if newly_unlocked:
        await session.flush()

    return newly_unlocked
