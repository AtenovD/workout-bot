"""
Workout Generator — generates WorkoutSession exercises from DB based on user profile.
"""
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, or_

from models.profile import Profile, Goal, TrainingStructure
from models.exercise import Exercise, Equipment, EquipmentCategory, ExerciseType, MuscleGroup
from models.workout import SessionExercise, WorkoutSession, ExerciseSet

FULLBODY_GROUPS = ["chest", "back", "legs", "shoulders", "biceps", "triceps", "core"]

SPLIT_ROTATIONS = {
    "upper_lower": [
        ["chest", "back", "shoulders", "biceps", "triceps"],
        ["legs", "glutes", "calves", "core"],
    ],
    "push_pull_legs": [
        ["chest", "shoulders", "triceps"],
        ["back", "biceps"],
        ["legs", "glutes", "calves"],
    ],
    "bro_split": [
        ["chest", "triceps"], ["back", "biceps"],
        ["shoulders", "traps"], ["legs", "glutes"],
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
    "hard":  {"sets": 1,  "weight_pct": 1.15, "rest_factor": 1.25},
}

HEALTH_EXCLUSIONS = {
    "lower_back_pain": ["deadlift", "good_morning", "hyperextension", "stiff_leg"],
    "knee_injury":     ["deep_squat", "full_lunge", "box_jump"],
    "shoulder_issue":  ["overhead_press", "upright_row", "behind_neck"],
    "hernia":          ["deadlift", "heavy_squat", "leg_press"],
}

GROUP_ALIASES = {
    "chest": ["chest", "upper_chest", "lower_chest"],
    "back": ["lats", "middle_back", "lower_back", "back"],
    "legs": ["quadriceps", "hamstrings", "legs"],
    "quads": ["quadriceps", "quads", "legs"],
    "shoulders": ["front_delts", "side_delts", "rear_delts", "shoulders"],
    "biceps": ["biceps", "arms"],
    "triceps": ["triceps", "arms"],
    "core": ["abs", "obliques", "core"],
    "glutes": ["glutes"],
    "calves": ["calves"],
    "traps": ["traps"],
}

MAJOR_GROUPS = {
    "chest", "upper_chest", "lower_chest", "back", "lats", "middle_back",
    "quadriceps", "quads", "legs", "hamstrings", "glutes",
}

STARTING_WEIGHTS = {
    ExerciseType.compound: 40.0,
    ExerciseType.isolation: 10.0,
    ExerciseType.cardio: 0.0,
    ExerciseType.mobility: 0.0,
}

BODYWEIGHT_EQUIPMENT_CODES = {"bodyweight", "pullup_bar", "dip_bar", "gymnastics_rings", "trx"}
CODE_REQUIRED_EQUIPMENT = {
    "trx": "trx",
}


def _is_excluded(code: str, health_flags: list) -> bool:
    for flag in (health_flags or []):
        if flag == "none": continue
        for prefix in HEALTH_EXCLUSIONS.get(flag, []):
            if code.startswith(prefix):
                return True
    return False


def _resolve_muscle_groups(target_groups: list[str], available: dict[str, int]) -> list[tuple[str, int]]:
    resolved: list[tuple[str, int]] = []
    seen: set[int] = set()
    for target in target_groups:
        for code in GROUP_ALIASES.get(target, [target]):
            mg_id = available.get(code)
            if mg_id and mg_id not in seen:
                resolved.append((code, mg_id))
                seen.add(mg_id)
    return resolved


def _is_equipment_available(
    ex: Exercise,
    user_equipment_ids: set[int],
    selected_equipment_codes: set[str] | None = None,
) -> bool:
    selected_equipment_codes = selected_equipment_codes or set()
    for code_prefix, required_code in CODE_REQUIRED_EQUIPMENT.items():
        if ex.code.startswith(f"{code_prefix}_") and required_code not in selected_equipment_codes:
            return False
    if ex.equipment_category == EquipmentCategory.none:
        return True
    return bool(ex.required_equipment_id and ex.required_equipment_id in user_equipment_ids)


def _exercise_score(ex: Exercise, user_equipment_ids: set[int], modifier: str, has_weighted_equipment: bool) -> int:
    score = 0
    if ex.required_equipment_id and ex.required_equipment_id in user_equipment_ids:
        score += 100
    if ex.equipment_category != EquipmentCategory.none:
        score += 25
    elif has_weighted_equipment:
        score -= 90

    if ex.exercise_type == ExerciseType.compound:
        score += 30 if modifier == "hard" else 15
    elif ex.exercise_type == ExerciseType.isolation:
        score += 10
    elif ex.exercise_type in {ExerciseType.cardio, ExerciseType.mobility}:
        score -= 200

    difficulty = int(ex.difficulty or 1)
    if modifier == "hard":
        score += difficulty * 6
    elif modifier == "light":
        score -= difficulty * 4
    else:
        score += difficulty * 2
    return score


def _rank_pool(pool: list[Exercise], user_equipment_ids: set[int], modifier: str, has_weighted_equipment: bool) -> list[Exercise]:
    return sorted(
        pool,
        key=lambda ex: (
            _exercise_score(ex, user_equipment_ids, modifier, has_weighted_equipment),
            int(ex.difficulty or 1),
            ex.name_ru or ex.name_en or ex.code,
        ),
        reverse=True,
    )


def _target_reps_range(goal: Goal, modifier: str, exercise_type: ExerciseType) -> tuple[int, int]:
    if modifier == "hard":
        if exercise_type == ExerciseType.compound:
            return (5, 8)
        if exercise_type == ExerciseType.isolation:
            return (8, 12)
        return (8, 12)
    return GOAL_PARAMS[goal]["reps"]


def _starting_weight_for(ex: Exercise, equipment_codes_by_id: dict[int, str]) -> float:
    equipment_code = equipment_codes_by_id.get(ex.required_equipment_id or 0)
    if ex.equipment_category == EquipmentCategory.none or equipment_code in BODYWEIGHT_EQUIPMENT_CODES:
        return 0.0
    return STARTING_WEIGHTS.get(ex.exercise_type, 20.0)


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
    user_equipment_ids = set(user_equipment_ids or [])
    eq_res = await session.execute(select(Equipment).where(Equipment.id.in_(list(user_equipment_ids)))) if user_equipment_ids else None
    equipment_codes_by_id = {eq.id: eq.code for eq in eq_res.scalars().all()} if eq_res else {}
    selected_equipment_codes = set(equipment_codes_by_id.values())
    has_weighted_equipment = any(code not in BODYWEIGHT_EQUIPMENT_CODES for code in selected_equipment_codes)

    # Determine target groups
    if profile.training_structure == TrainingStructure.fullbody:
        target_groups = FULLBODY_GROUPS
    else:
        split = profile.split_type.value if profile.split_type else "upper_lower"
        rotations = SPLIT_ROTATIONS.get(split, SPLIT_ROTATIONS["upper_lower"])
        target_groups = rotations[rotation_idx % len(rotations)]

    # Get muscle group IDs. Production data uses detailed codes (lats/quadriceps),
    # while tests and old installs may still use broad codes (back/legs).
    mg_res = await session.execute(select(MuscleGroup))
    available_groups = {mg.code: mg.id for mg in mg_res.scalars().all()}
    muscle_groups = _resolve_muscle_groups(target_groups, available_groups)
    muscle_group_ids = [mg_id for _, mg_id in muscle_groups]

    # Fetch exercises
    equipment_clause = (
        or_(Exercise.equipment_category == EquipmentCategory.none,
            Exercise.required_equipment_id.in_(list(user_equipment_ids)))
        if user_equipment_ids
        else Exercise.equipment_category == EquipmentCategory.none
    )
    candidates_res = await session.execute(
        select(Exercise).where(
            and_(
                Exercise.is_active == True,
                Exercise.primary_muscle_group_id.in_(muscle_group_ids),
                equipment_clause,
            )
        )
    )
    candidates = [
        e for e in candidates_res.scalars().all()
        if _is_equipment_available(e, user_equipment_ids, selected_equipment_codes) and not _is_excluded(e.code, health_flags)
    ]

    # Group by muscle group ID
    by_mg: dict[int, list[Exercise]] = {}
    for ex in candidates:
        mid = ex.primary_muscle_group_id
        by_mg.setdefault(mid, []).append(ex)

    # Select exercises
    selected: list[Exercise] = []
    seen_ids: set[int] = set()
    for code, mg_id in muscle_groups:
        pool = by_mg.get(mg_id, [])
        if not pool: continue
        ranked = _rank_pool(pool, user_equipment_ids, modifier, has_weighted_equipment)
        compounds = [e for e in ranked if e.exercise_type == ExerciseType.compound]
        isolations = [e for e in ranked if e.exercise_type == ExerciseType.isolation]
        is_major = code in MAJOR_GROUPS
        chosen = []
        if compounds:
            chosen.append(compounds[0])
        if is_major and isolations:
            chosen.append(isolations[0])
        elif not compounds and isolations:
            chosen.append(isolations[0])
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
    if modifier == "hard":
        rest_secs = max(rest_secs, 120)
    time_per_ex = sets_count * (45 + rest_secs) / 60
    max_ex = max(3, int((profile.preferred_duration_min or 45) / time_per_ex))
    selected = selected[:max_ex]

    # Assign volume and save
    from services.progression import calculate_next_weight
    result_list = []
    for idx, ex in enumerate(selected):
        reps_min, reps_max = _target_reps_range(goal, modifier, ex.exercise_type)
        target_reps = random.randint(reps_min, reps_max)
        last_w = await _get_last_weight(session, profile.user_id, ex.id)
        start_weight = _starting_weight_for(ex, equipment_codes_by_id)
        if start_weight == 0.0 and last_w is None:
            weight = 0.0
        else:
            weight = calculate_next_weight(
                last_weight_kg=last_w if last_w is not None else start_weight,
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
