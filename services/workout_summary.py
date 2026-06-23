"""
Workout Summary Service — generates a detailed post-workout comparison
with the previous session. Shows per-exercise weight delta, PR flags,
weekly stats and streak.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import date, timedelta
from dataclasses import dataclass, field
from typing import Optional

from models.workout import WorkoutSession, SessionExercise, ExerciseSet, SessionStatus
from models.gamification import UserStats
from models.personal_record import PersonalRecord
from models.exercise import Exercise
from services.gamification import get_level_from_xp, get_title


@dataclass
class ExerciseResult:
    name: str
    sets_done: int
    avg_reps: int
    best_weight: float
    total_volume: float
    prev_best_weight: Optional[float] = None
    prev_total_volume: Optional[float] = None


@dataclass
class WorkoutSummary:
    duration_min: int
    total_volume: float
    calories: int
    xp_earned: int
    level: int
    level_up: bool
    streak: int
    exercises: list[ExerciseResult] = field(default_factory=list)
    prs: list[str] = field(default_factory=list)
    weekly_workouts: int = 0
    weekly_volume: float = 0.0
    prev_session_volume: Optional[float] = None


async def build_workout_summary(
    session: AsyncSession,
    user_id: int,
    workout_id: int,
    xp_earned: int,
    old_level: int,
) -> WorkoutSummary:
    ws = await session.get(WorkoutSession, workout_id)
    stats_res = await session.execute(select(UserStats).where(UserStats.user_id == user_id))
    stats = stats_res.scalar_one()

    # Current session exercises
    result = await session.execute(
        select(SessionExercise, Exercise)
        .join(Exercise, SessionExercise.exercise_id == Exercise.id)
        .where(SessionExercise.session_id == workout_id)
        .order_by(SessionExercise.order_index)
    )
    se_rows = result.all()

    exercises: list[ExerciseResult] = []
    for se, ex in se_rows:
        sets_res = await session.execute(
            select(ExerciseSet).where(
                ExerciseSet.session_exercise_id == se.id,
                ExerciseSet.is_done == True,
            )
        )
        sets = sets_res.scalars().all()
        if not sets:
            continue

        total_vol = sum(float(s.weight_kg or 0) * (s.reps_done or 0) for s in sets)
        best_w = max((float(s.weight_kg or 0) for s in sets), default=0.0)
        avg_reps = round(sum(s.reps_done or 0 for s in sets) / len(sets))

        # Last session same exercise
        prev_res = await session.execute(
            select(ExerciseSet)
            .join(SessionExercise, ExerciseSet.session_exercise_id == SessionExercise.id)
            .join(WorkoutSession, SessionExercise.session_id == WorkoutSession.id)
            .where(
                WorkoutSession.user_id == user_id,
                WorkoutSession.id != workout_id,
                WorkoutSession.status == SessionStatus.completed,
                SessionExercise.exercise_id == ex.id,
                ExerciseSet.is_done == True,
            )
            .order_by(desc(WorkoutSession.completed_at))
            .limit(20)
        )
        prev_sets = prev_res.scalars().all()
        prev_best_w = max((float(s.weight_kg or 0) for s in prev_sets), default=None) if prev_sets else None
        prev_vol = sum(float(s.weight_kg or 0) * (s.reps_done or 0) for s in prev_sets) if prev_sets else None

        exercises.append(ExerciseResult(
            name=ex.name_ru,
            sets_done=len(sets),
            avg_reps=avg_reps,
            best_weight=best_w,
            total_volume=total_vol,
            prev_best_weight=prev_best_w,
            prev_total_volume=prev_vol,
        ))

    # Weekly stats
    week_ago = date.today() - timedelta(days=7)
    weekly_res = await session.execute(
        select(func.count(), func.sum(WorkoutSession.total_volume_kg))
        .where(
            WorkoutSession.user_id == user_id,
            WorkoutSession.status == SessionStatus.completed,
            WorkoutSession.scheduled_date >= week_ago,
        )
    )
    wc, wv = weekly_res.one()

    # Previous session total volume
    prev_session_res = await session.execute(
        select(WorkoutSession.total_volume_kg)
        .where(
            WorkoutSession.user_id == user_id,
            WorkoutSession.id != workout_id,
            WorkoutSession.status == SessionStatus.completed,
        )
        .order_by(desc(WorkoutSession.completed_at))
        .limit(1)
    )
    prev_vol_row = prev_session_res.scalar_one_or_none()

    # PRs set this session
    pr_res = await session.execute(
        select(PersonalRecord, Exercise)
        .join(Exercise, PersonalRecord.exercise_id == Exercise.id)
        .where(PersonalRecord.user_id == user_id, PersonalRecord.set_at_session_id == workout_id)
    )
    prs = [f"🏆 <b>PR:</b> {ex.name_ru} — {pr.max_weight:.1f} кг" for pr, ex in pr_res.all()]

    return WorkoutSummary(
        duration_min=ws.duration_min or 0,
        total_volume=float(ws.total_volume_kg or 0),
        calories=ws.calories_burned or 0,
        xp_earned=xp_earned,
        level=stats.level,
        level_up=stats.level > old_level,
        streak=stats.current_streak,
        exercises=exercises,
        prs=prs,
        weekly_workouts=wc or 0,
        weekly_volume=float(wv or 0),
        prev_session_volume=float(prev_vol_row) if prev_vol_row else None,
    )


def format_summary_message(s: WorkoutSummary) -> str:
    lines = []

    if s.level_up:
        lines.append(f"🎉 <b>УРОВЕНЬ {s.level} — {get_title(s.level)}!</b>")
        lines.append("")

    lines.append("🏁 <b>Тренировка завершена!</b>")
    lines.append("")

    # Total volume delta vs previous session
    vol_delta = ""
    if s.prev_session_volume and s.prev_session_volume > 0:
        delta = s.total_volume - s.prev_session_volume
        pct = delta / s.prev_session_volume * 100
        arrow = "📈" if delta >= 0 else "📉"
        vol_delta = f" {arrow} {'+' if delta >= 0 else ''}{delta:.0f} кг ({pct:+.0f}%)"

    lines.append(f"⏱ <b>{s.duration_min} мин</b>  ·  🏋️ <b>{s.total_volume:.0f} кг{vol_delta}</b>")
    lines.append(f"🔥 ~{s.calories} ккал  ·  ⭐ +{s.xp_earned} XP  ·  🔥 Стрик {s.streak} дн.")
    lines.append("")

    # Per-exercise breakdown
    if s.exercises:
        lines.append("📋 <b>Детально:</b>")
        for ex in s.exercises:
            w_delta = ""
            if ex.prev_best_weight is not None:
                diff = ex.best_weight - ex.prev_best_weight
                if abs(diff) >= 0.01:
                    arrow = "↑" if diff > 0 else "↓"
                    w_delta = f" <b>{arrow}{abs(diff):.1f} кг</b>"
            lines.append(
                f"  • {ex.name} — {ex.sets_done}×{ex.avg_reps} "
                f"@ {ex.best_weight:.1f} кг{w_delta}"
            )
        lines.append("")

    # PRs
    if s.prs:
        lines.extend(s.prs)
        lines.append("")

    # Weekly
    lines.append(f"📅 Неделя: <b>{s.weekly_workouts} тр. · {s.weekly_volume:.0f} кг</b>")

    return "\n".join(lines)
