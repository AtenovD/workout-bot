"""
Calories burned calculator using MET values.

The bot cannot know exact energy expenditure without sensor data, so these
functions return a conservative estimate built from workout content, profile
data, and logged effort.
"""

from datetime import date

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.exercise import EquipmentCategory, Exercise, ExerciseType
from models.profile import ExperienceLevel, Gender, Profile
from models.workout import DifficultyModifier, ExerciseSet, SessionExercise, WorkoutSession

DEFAULT_MET = {
    "compound": 6.0,
    "isolation": 4.0,
    "cardio": 8.0,
    "mobility": 2.5,
}

DIFFICULTY_FACTOR = {
    DifficultyModifier.light: 0.88,
    DifficultyModifier.normal: 1.0,
    DifficultyModifier.hard: 1.15,
    "light": 0.88,
    "normal": 1.0,
    "hard": 1.15,
}

EXPERIENCE_FACTOR = {
    ExperienceLevel.beginner: 0.96,
    ExperienceLevel.intermediate: 1.02,
    ExperienceLevel.advanced: 1.07,
    "beginner": 0.96,
    "intermediate": 1.02,
    "advanced": 1.07,
}


def calculate_calories_burned(met: float, body_weight_kg: float, duration_min: int) -> int:
    """
    Calculate calories burned during workout.
    
    Args:
        met: MET value for activity type
        body_weight_kg: User's body weight in kg
        duration_min: Duration in minutes
    
    Returns:
        Calories burned (kcal) as integer
    """
    hours = duration_min / 60.0
    calories = met * body_weight_kg * hours
    return max(1, round(calories))


def estimate_workout_calories(
    exercises: list[dict],
    body_weight_kg: float,
    duration_min: int,
) -> int:
    """
    Estimate total calories for a workout session.
    Uses weighted average of MET values.
    """
    if not exercises:
        return calculate_calories_burned(DEFAULT_MET["compound"], body_weight_kg, duration_min)
    
    total_met = sum(e.get("met", DEFAULT_MET["compound"]) for e in exercises)
    avg_met = total_met / len(exercises)
    return calculate_calories_burned(avg_met, body_weight_kg, duration_min)


def _profile_age(profile: Profile | None) -> int | None:
    if not profile or not profile.birth_date:
        return None
    return max(1, date.today().year - profile.birth_date.year)


def _age_factor(age: int | None) -> float:
    if not age:
        return 1.0
    if age < 30:
        return 1.03
    if age < 45:
        return 1.0
    if age < 60:
        return 0.97
    return 0.93


def _gender_factor(gender: Gender | str | None) -> float:
    if gender == Gender.male or gender == "male":
        return 1.03
    if gender == Gender.female or gender == "female":
        return 0.97
    return 1.0


def _exercise_met(exercise: Exercise, *, is_warmup: bool = False) -> float:
    if exercise.met_value and exercise.met_value > 0:
        base = float(exercise.met_value)
    else:
        exercise_type = exercise.exercise_type.value if exercise.exercise_type else "compound"
        base = DEFAULT_MET.get(exercise_type, DEFAULT_MET["compound"])
        if exercise.equipment_category == EquipmentCategory.none and exercise.exercise_type == ExerciseType.compound:
            base = min(base, 5.2)

    if is_warmup:
        return max(2.5, base * 0.58)
    return base


def _duration_from_plan(rows: list[tuple[SessionExercise, Exercise, int, int]]) -> int:
    minutes = 8.0
    for session_exercise, _, work_sets, warmup_sets in rows:
        sets = work_sets or int(session_exercise.target_sets or 0)
        warmups = warmup_sets or 0
        rest_min = float(session_exercise.rest_seconds or 90) / 60.0
        minutes += sets * 1.0 + warmups * 0.6 + max(0, sets - 1) * rest_min
    return max(10, round(minutes))


def _volume_factor(total_volume_kg: float, body_weight_kg: float, duration_min: int) -> float:
    if total_volume_kg <= 0 or body_weight_kg <= 0 or duration_min <= 0:
        return 1.0
    density = total_volume_kg / max(1.0, body_weight_kg * duration_min)
    if density >= 1.8:
        return 1.10
    if density >= 1.2:
        return 1.05
    if density <= 0.25:
        return 0.92
    return 1.0


async def estimate_completed_workout_calories(
    session: AsyncSession,
    user_id: int,
    workout_session_id: int,
) -> int:
    """Estimate kcal for a completed workout from real user/session data."""

    workout = await session.get(WorkoutSession, workout_session_id)
    if not workout:
        return 0

    profile = (
        await session.execute(select(Profile).where(Profile.user_id == user_id))
    ).scalar_one_or_none()
    body_weight = float(profile.current_weight_kg or 75) if profile else 75.0

    rows_raw = (
        await session.execute(
            select(
                SessionExercise,
                Exercise,
                func.sum(
                    case((ExerciseSet.is_warmup == False, 1), else_=0)
                ).label("work_sets"),
                func.sum(
                    case((ExerciseSet.is_warmup == True, 1), else_=0)
                ).label("warmup_sets"),
            )
            .join(Exercise, SessionExercise.exercise_id == Exercise.id)
            .outerjoin(ExerciseSet, ExerciseSet.session_exercise_id == SessionExercise.id)
            .where(SessionExercise.session_id == workout_session_id)
            .group_by(SessionExercise.id, Exercise.id)
            .order_by(SessionExercise.order_index)
        )
    ).all()

    rows: list[tuple[SessionExercise, Exercise, int, int]] = [
        (se, ex, int(work_sets or 0), int(warmup_sets or 0))
        for se, ex, work_sets, warmup_sets in rows_raw
        if not se.was_skipped
    ]

    duration_min = int(workout.duration_min or 0)
    if duration_min < 5:
        duration_min = int(profile.preferred_duration_min or 0) if profile else 0
    if duration_min < 5:
        duration_min = _duration_from_plan(rows)

    if not rows:
        met = DEFAULT_MET["compound"]
    else:
        weighted_met = 0.0
        total_units = 0.0
        for session_exercise, exercise, work_sets, warmup_sets in rows:
            work_units = float(work_sets or session_exercise.target_sets or 1)
            warmup_units = float(warmup_sets or 0) * 0.6
            weighted_met += _exercise_met(exercise) * work_units
            weighted_met += _exercise_met(exercise, is_warmup=True) * warmup_units
            total_units += work_units + warmup_units
        met = weighted_met / max(1.0, total_units)

    total_volume = float(workout.total_volume_kg or 0)
    factor = (
        DIFFICULTY_FACTOR.get(workout.difficulty_modifier, 1.0)
        * EXPERIENCE_FACTOR.get(profile.experience_level if profile else None, 1.0)
        * _gender_factor(profile.gender if profile else None)
        * _age_factor(_profile_age(profile))
        * _volume_factor(total_volume, body_weight, duration_min)
    )

    return calculate_calories_burned(met * factor, body_weight, duration_min)
