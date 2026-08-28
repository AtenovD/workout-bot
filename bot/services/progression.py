from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from models.personal_record import PersonalRecord
from models.workout import WorkoutSession, SessionExercise, ExerciseSet, SessionStatus
from models.exercise import Exercise


async def calculate_starting_weight(session: AsyncSession, user_id: int, exercise_id: int, modifier: str) -> float:
    """Calculate starting weight based on PersonalRecord and progression."""
    # Get latest PR
    pr_res = await session.execute(
        select(PersonalRecord).where(
            PersonalRecord.user_id == user_id,
            PersonalRecord.exercise_id == exercise_id
        ).order_by(desc(PersonalRecord.value)).limit(1)
    )
    pr = pr_res.scalar()
    
    if not pr:
        return 0.0
    
    base_weight = float(pr.value)
    
    # Apply modifier
    multipliers = {"easy": 0.70, "normal": 0.80, "hard": 0.85}
    mult = multipliers.get(modifier, 0.80)
    
    return round(base_weight * mult, 2)


async def calculate_target_reps(exercise: Exercise, modifier: str) -> int:
    """Calculate target reps based on exercise type and modifier."""
    base_reps = {"easy": 12, "normal": 10, "hard": 8}
    return base_reps.get(modifier, 10)


async def calculate_target_sets(modifier: str) -> int:
    return {"easy": 3, "normal": 3, "hard": 4}.get(modifier, 3)
