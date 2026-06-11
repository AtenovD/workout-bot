"""
Workout Generator — generates WorkoutSession exercises from DB based on user profile.
"""
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from models.profile import Profile, Goal, TrainingStructure
from models.exercise import Exercise, EquipmentCategory, ExerciseType, MuscleGroup
from models.workout import SessionExercise, WorkoutSession, ExerciseSet

FULLBODY_GROUPS = ["chest", "back", "quads", "hamstrings", "shoulders", "biceps", "triceps", "core"]

SPLIT_ROTATIONS = {
    "upper_lower": [
        ["chest", "back", "shoulders", "biceps", "triceps"],
        ["quads", "hamstrings", "glutes", "calves", "core"],
    ],
    "push_pull_legs": [
        ["chest", "shoulders", "triceps"],
        ["back", "biceps"],
        ["quads", "hamstrings", "glutes", "calves"],
    ],
    "bro_split": [
        ["chest", "triceps"], ["back", "biceps"],
        ["shoulders", "traps"], ["quads", "hamstrings", "glutes"],
        ["biceps", "triceps"],
    ],
}

GOAL_PARAMS = {
    Goal.mass_gain:   {"reps": (8, 12),  "sets": 4, "rest": 105},
    Goal.weight_loss: {"reps": (12, 18), "sets": 3, "rest": 45},
    Goal.maintenance: {"reps": (10, 12), "sets": 3, "rest": 75},
    Goal.cardio:      {"reps": (15, 20), "sets": 3, "rest": 30},
}

MODIFIER_DELTA = {
    "light": {"sets": -1, "weight_pct": 0.85, "rest_factor": 1.3},
    "normal": {"sets": 0,  "weight_pct": 1.0,  "rest_factor": 1.0},
    "hard":  {"sets": 1,  "weight_pct": 1.1,  "rest_factor": 0.8},
}

HEALTH_EXCLUSIONS = {
    "lower_back_pain": ["deadlift", "good_morning", "hyperextension", "stiff_leg"],
    "knee_injury":     ["deep_squat", "full_lunge", "box_jump"],
    "shoulder_issue":  ["overhead_press", "upright_row", "behind_neck"],
    "hernia":          ["deadlift", "heavy_squat", "leg_press"],
}

MAJOR_GROUPS = {"chest", "back", "quads", "hamstrings", "glutes"}

STARTING_WEIGHTS = {
    ExerciseType.compound: 40.0,
    ExerciseType.isolation: 10.0,
    ExerciseType.cardio: 0.0,
    ExerciseType.mobility: 0.0,
}


def _is_excluded(code: str, health_flags: list) -> bool:
    for flag in (health_flags or []):
        if flag == "none": continue
        for prefix in HEALTH_EXCLUSIONS.get(flag, []):
            if code.startswith(prefix):
                return True
    return False


async def _get_rotation_idx(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(
        select(WorkoutSession)
        .where(WorkoutSession.user_id == user_id, WorkoutSession.status == "completed")
        .order_by(desc(WorkoutSession.created_at)).limit(1)
    )
    last = result.scalar_one_or_none()
    if last and last.notes and last.notes.startswith("rot:"):
        return int(last.notes.split(":")[1]) + 1
    return 0


async def _get_last_weight(session: AsyncSession, user_id: int, exercise_id: int) -> float | None:
    result = await session.execute(
        select(ExerciseSet.weight_kg)
        .join(SessionExercise)
        .join(WorkoutSession)
        .where(WorkoutSession.user_id == user_id,
               SessionExercise.exercise_id == exercise_id,
               ExerciseSet.is_warmup == False)
        .order_by(desc(ExerciseSet.completed_at)).limit(1)
    )
    row = result.scalar_one_or_none()
    return float(row) if row else None


async def generate_workout_session(
    session: AsyncSession,
    profile: Profile,
    user_equipment_ids: list[int],
    workout_session_id: int,
    modifier: str = "normal",
) -> list[tuple[SessionExercise, Exercise]]:
    rotation_idx = await _get_rotation_idx(session, profile.user_id)
    health_flags = profile.health_flags or []

    # Determine target groups
    if profile.training_structure == TrainingStructure.fullbody:
        target_groups = FULLBODY_GROUPS
    else:
        split = profile.split_type.value if profile.split_type else "upper_lower"
        rotations = SPLIT_ROTATIONS.get(split, SPLIT_ROTATIONS["upper_lower"])
        target_groups = rotations[rotation_idx % len(rotations)]

    # Get muscle group IDs
    mg_res = await session.execute(select(MuscleGroup).where(MuscleGroup.code.in_(target_groups)))
    muscle_groups = {mg.code: mg.id for mg in mg_res.scalars().all()}

    # Fetch exercises
    candidates_res = await session.execute(
        select(Exercise).where(
            and_(
                Exercise.is_active == True,
                Exercise.primary_muscle_group_id.in_(list(muscle_groups.values())),
                (Exercise.equipment_category == EquipmentCategory.none) |
                (Exercise.required_equipment_id.in_(user_equipment_ids)) |
                (Exercise.required_equipment_id.is_(None))
            )
        )
    )
    candidates = [e for e in candidates_res.scalars().all() if not _is_excluded(e.code, health_flags)]

    # Group by muscle group ID
    by_mg: dict[int, list[Exercise]] = {}
    for ex in candidates:
        mid = ex.primary_muscle_group_id
        by_mg.setdefault(mid, []).append(ex)

    # Select exercises
    selected: list[Exercise] = []
    seen_ids: set[int] = set()
    for code, mg_id in muscle_groups.items():
        pool = by_mg.get(mg_id, [])
        if not pool: continue
        compounds = [e for e in pool if e.exercise_type == ExerciseType.compound]
        isolations = [e for e in pool if e.exercise_type == ExerciseType.isolation]
        is_major = code in MAJOR_GROUPS
        chosen = []
        if compounds:
            chosen.append(random.choice(compounds))
        if is_major and isolations:
            chosen.append(random.choice(isolations))
        elif not compounds and isolations:
            chosen.append(random.choice(isolations))
        for ex in chosen:
            if ex.id not in seen_ids:
                seen_ids.add(ex.id)
                selected.append(ex)

    # Limit by duration
    goal = profile.goal or Goal.maintenance
    params = GOAL_PARAMS[goal]
    mod = MODIFIER_DELTA[modifier]
    sets_count = max(1, params["sets"] + mod["sets"])
    rest_secs = round(params["rest"] * mod["rest_factor"])
    time_per_ex = sets_count * (45 + rest_secs) / 60
    max_ex = max(3, int((profile.preferred_duration_min or 45) / time_per_ex))
    selected = selected[:max_ex]

    # Assign volume and save
    from services.progression import calculate_next_weight
    result_list = []
    for idx, ex in enumerate(selected):
        reps_min, reps_max = params["reps"]
        target_reps = random.randint(reps_min, reps_max)
        last_w = await _get_last_weight(session, profile.user_id, ex.id)
        weight = calculate_next_weight(
            last_weight_kg=last_w or STARTING_WEIGHTS.get(ex.exercise_type, 20.0),
            last_reps_done=target_reps, target_reps=target_reps,
            last_rpe=None, exercise_type=ex.exercise_type.value, difficulty_modifier=modifier,
        )
        weight *= mod["weight_pct"]
        weight = round(weight, 2)

        se = SessionExercise(
            session_id=workout_session_id, exercise_id=ex.id, order_index=idx,
            target_sets=sets_count, target_reps=target_reps, target_weight_kg=weight, rest_seconds=rest_secs,
        )
        session.add(se)
        result_list.append((se, ex))

    ws = await session.get(WorkoutSession, workout_session_id)
    if ws: ws.notes = f"rot:{rotation_idx}"
    await session.flush()
    return result_list
