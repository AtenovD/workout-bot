from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import select

from models.exercise import Exercise
from models.profile import ExperienceLevel, Profile
from models.workout import DifficultyModifier, ExerciseSet, SessionExercise, SessionStatus, WorkoutSession
from services.calories import estimate_completed_workout_calories


@pytest.mark.asyncio
async def test_completed_workout_calories_use_profile_and_logged_exercises(session, registered_user):
    profile = (
        await session.execute(select(Profile).where(Profile.user_id == registered_user.id))
    ).scalar_one()
    profile.current_weight_kg = 100
    profile.experience_level = ExperienceLevel.advanced

    bench = (
        await session.execute(select(Exercise).where(Exercise.code == "bench_press"))
    ).scalar_one()
    squat = (
        await session.execute(select(Exercise).where(Exercise.code == "barbell_squat"))
    ).scalar_one()

    workout = WorkoutSession(
        user_id=registered_user.id,
        status=SessionStatus.completed,
        difficulty_modifier=DifficultyModifier.hard,
        scheduled_date=date.today(),
        started_at=datetime.utcnow() - timedelta(minutes=60),
        completed_at=datetime.utcnow(),
        duration_min=60,
        total_volume_kg=7200,
    )
    session.add(workout)
    await session.flush()

    session_exercises = [
        SessionExercise(session_id=workout.id, exercise_id=bench.id, order_index=0, target_sets=4, target_reps=8, target_weight_kg=100, rest_seconds=120),
        SessionExercise(session_id=workout.id, exercise_id=squat.id, order_index=1, target_sets=4, target_reps=8, target_weight_kg=125, rest_seconds=150),
    ]
    session.add_all(session_exercises)
    await session.flush()

    for session_exercise in session_exercises:
        session.add(ExerciseSet(session_exercise_id=session_exercise.id, set_number=1, reps_done=8, weight_kg=session_exercise.target_weight_kg, is_warmup=False))
        session.add(ExerciseSet(session_exercise_id=session_exercise.id, set_number=2, reps_done=8, weight_kg=session_exercise.target_weight_kg, is_warmup=False))
        session.add(ExerciseSet(session_exercise_id=session_exercise.id, set_number=1, reps_done=5, weight_kg=float(session_exercise.target_weight_kg or 0) * 0.6, is_warmup=True))
    await session.flush()

    calories = await estimate_completed_workout_calories(session, registered_user.id, workout.id)

    assert 650 <= calories <= 900


@pytest.mark.asyncio
async def test_completed_workout_calories_fallback_to_profile_duration_when_timer_is_too_short(session, registered_user):
    profile = (
        await session.execute(select(Profile).where(Profile.user_id == registered_user.id))
    ).scalar_one()
    profile.current_weight_kg = 80
    profile.preferred_duration_min = 45

    bench = (
        await session.execute(select(Exercise).where(Exercise.code == "bench_press"))
    ).scalar_one()
    workout = WorkoutSession(
        user_id=registered_user.id,
        status=SessionStatus.completed,
        difficulty_modifier=DifficultyModifier.light,
        scheduled_date=date.today(),
        duration_min=0,
        total_volume_kg=1600,
    )
    session.add(workout)
    await session.flush()

    session_exercise = SessionExercise(
        session_id=workout.id,
        exercise_id=bench.id,
        order_index=0,
        target_sets=2,
        target_reps=10,
        target_weight_kg=80,
        rest_seconds=90,
    )
    session.add(session_exercise)
    await session.flush()
    session.add(ExerciseSet(session_exercise_id=session_exercise.id, set_number=1, reps_done=10, weight_kg=80, is_warmup=False))
    session.add(ExerciseSet(session_exercise_id=session_exercise.id, set_number=2, reps_done=10, weight_kg=80, is_warmup=False))
    await session.flush()

    calories = await estimate_completed_workout_calories(session, registered_user.id, workout.id)

    assert 230 <= calories <= 340
