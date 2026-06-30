"""
Workout Generator — generates WorkoutSession exercises from DB based on user profile.
"""
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, or_

from models.profile import Profile, Goal, TrainingStructure
from models.exercise import Exercise, Equipment, EquipmentCategory, ExerciseType, MuscleGroup
from models.workout import SessionExercise, WorkoutSession, ExerciseSet, WorkoutReview
from services.strength_calibration import calibrated_start_weight
from services.training_strategy import parse_strategy_note, strategy_context_for_next_session

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

REVIEW_ADJUSTMENTS = {
    "harder": {"sets_delta": 0, "weight_factor": 1.05, "rest_factor": 1.0},
    "ok": {"sets_delta": 0, "weight_factor": 1.0, "rest_factor": 1.0},
    "easier": {"sets_delta": -1, "weight_factor": 0.9, "rest_factor": 1.1},
}

PAIN_ADJUSTMENTS = {
    "none": {"sets_delta": 0, "weight_factor": 1.0, "rest_factor": 1.0},
    "discomfort": {"sets_delta": -1, "weight_factor": 0.9, "rest_factor": 1.15},
    "pain": {"sets_delta": -1, "weight_factor": 0.8, "rest_factor": 1.25},
}

HEALTH_EXCLUSIONS = {
    "lower_back_pain": ["deadlift", "good_morning", "hyperextension", "stiff_leg", "barbell_row"],
    "spinal_disc_hernia": ["deadlift", "good_morning", "hyperextension", "stiff_leg", "barbell_row", "squat_barbell"],
    "knee_injury": ["deep_squat", "full_lunge", "box_jump", "jump", "pistol_squat"],
    "knee_pain": ["deep_squat", "box_jump", "jump", "pistol_squat"],
    "shoulder_issue": ["overhead_press", "upright_row", "behind_neck", "arnold_press", "dip"],
    "hypertension": ["max_effort", "heavy_single"],
    "heart_condition": ["max_effort", "heavy_single", "burpee", "jump"],
    "hiatal_hernia": ["deadlift", "squat", "leg_press", "lunge", "ab_wheel", "crunch", "woodchop", "pull_through", "kettlebell_swing"],
    "inguinal_hernia": ["deadlift", "squat", "leg_press", "lunge", "ab_wheel", "crunch", "plank", "woodchop", "pull_through", "kettlebell_swing"],
    "umbilical_hernia": ["deadlift", "squat", "leg_press", "lunge", "ab_wheel", "crunch", "plank", "woodchop", "pull_through", "kettlebell_swing"],
    "hernia": ["deadlift", "squat", "leg_press", "lunge", "ab_wheel", "crunch", "plank", "woodchop", "pull_through", "kettlebell_swing"],
}

HEALTH_LOAD_ADJUSTMENTS = {
    "lower_back_pain": {"sets_delta": -1, "weight_factor": 0.9, "rest_factor": 1.1},
    "spinal_disc_hernia": {"sets_delta": -1, "weight_factor": 0.82, "rest_factor": 1.2},
    "knee_injury": {"sets_delta": -1, "weight_factor": 0.88, "rest_factor": 1.1},
    "knee_pain": {"sets_delta": -1, "weight_factor": 0.9, "rest_factor": 1.1},
    "shoulder_issue": {"sets_delta": -1, "weight_factor": 0.88, "rest_factor": 1.12},
    "hypertension": {"sets_delta": -1, "weight_factor": 0.85, "rest_factor": 1.25},
    "heart_condition": {"sets_delta": -1, "weight_factor": 0.8, "rest_factor": 1.3},
    "hiatal_hernia": {"sets_delta": -1, "weight_factor": 0.82, "rest_factor": 1.2},
    "inguinal_hernia": {"sets_delta": -1, "weight_factor": 0.8, "rest_factor": 1.25},
    "umbilical_hernia": {"sets_delta": -1, "weight_factor": 0.8, "rest_factor": 1.25},
    "hernia": {"sets_delta": -1, "weight_factor": 0.82, "rest_factor": 1.2},
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


def _normalize_health_flags(health_flags) -> list[str]:
    if isinstance(health_flags, dict):
        raw = health_flags.get("flags") or health_flags.get("selected") or []
    else:
        raw = health_flags or []
    return [flag for flag in raw if isinstance(flag, str)]


def _is_excluded(code: str, health_flags) -> bool:
    normalized_code = (code or "").lower()
    for flag in _normalize_health_flags(health_flags):
        if flag == "none": continue
        for prefix in HEALTH_EXCLUSIONS.get(flag, []):
            if prefix in normalized_code:
                return True
    return False


def _combine_health_adjustments(health_flags) -> dict[str, float | int]:
    adjustment = {"sets_delta": 0, "weight_factor": 1.0, "rest_factor": 1.0}
    for flag in _normalize_health_flags(health_flags):
        source = HEALTH_LOAD_ADJUSTMENTS.get(flag)
        if not source:
            continue
        adjustment["sets_delta"] += int(source.get("sets_delta", 0))
        adjustment["weight_factor"] *= float(source.get("weight_factor", 1.0))
        adjustment["rest_factor"] *= float(source.get("rest_factor", 1.0))
    adjustment["sets_delta"] = max(-2, min(0, int(adjustment["sets_delta"])))
    adjustment["weight_factor"] = max(0.7, min(1.0, float(adjustment["weight_factor"])))
    adjustment["rest_factor"] = max(1.0, min(1.45, float(adjustment["rest_factor"])))
    return adjustment


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
    if last and last.notes:
        note = parse_strategy_note(last.notes)
        try:
            return int(note.get("rot", "0")) + 1
        except ValueError:
            return 0
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


async def _get_last_review(session: AsyncSession, user_id: int) -> WorkoutReview | None:
    result = await session.execute(
        select(WorkoutReview)
        .where(WorkoutReview.user_id == user_id)
        .order_by(desc(WorkoutReview.created_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


def _combine_review_adjustments(review: WorkoutReview | None) -> dict[str, float | int]:
    adjustment = {
        "sets_delta": 0,
        "weight_factor": 1.0,
        "rest_factor": 1.0,
        "avoid_exercise_codes": [],
        "prefer_exercise_codes": [],
        "reduce_muscle_groups": [],
        "focus_muscle_groups": [],
    }
    if not review:
        return adjustment

    for source in (
        REVIEW_ADJUSTMENTS.get(review.intensity_feedback or "", {}),
        PAIN_ADJUSTMENTS.get(review.pain_feedback or "", {}),
        getattr(review, "ai_adjustment", None) or {},
    ):
        adjustment["sets_delta"] += int(source.get("sets_delta", 0))
        adjustment["weight_factor"] *= float(source.get("weight_factor", 1.0))
        adjustment["rest_factor"] *= float(source.get("rest_factor", 1.0))
        for key in ("avoid_exercise_codes", "prefer_exercise_codes", "reduce_muscle_groups", "focus_muscle_groups"):
            values = source.get(key) or []
            if isinstance(values, list):
                adjustment[key] = list(dict.fromkeys([*adjustment[key], *[v for v in values if isinstance(v, str)]]))[:8]

    adjustment["sets_delta"] = max(-2, min(1, int(adjustment["sets_delta"])))
    adjustment["weight_factor"] = max(0.75, min(1.1, float(adjustment["weight_factor"])))
    adjustment["rest_factor"] = max(0.85, min(1.35, float(adjustment["rest_factor"])))
    return adjustment


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
    last_review = await _get_last_review(session, profile.user_id)
    review_adjustment = _combine_review_adjustments(last_review)
    health_adjustment = _combine_health_adjustments(health_flags)
    recent_skipped_ids = set(last_review.skipped_exercise_ids or []) if last_review else set()
    avoid_exercise_codes = set(review_adjustment.get("avoid_exercise_codes") or [])
    prefer_exercise_codes = set(review_adjustment.get("prefer_exercise_codes") or [])
    reduce_muscle_groups = set(review_adjustment.get("reduce_muscle_groups") or [])
    focus_muscle_groups = set(review_adjustment.get("focus_muscle_groups") or [])

    # Determine target groups
    if profile.training_structure == TrainingStructure.fullbody:
        target_groups = FULLBODY_GROUPS
    else:
        split = profile.split_type.value if profile.split_type else "upper_lower"
        rotations = SPLIT_ROTATIONS.get(split, SPLIT_ROTATIONS["upper_lower"])
        target_groups = rotations[rotation_idx % len(rotations)]

    strategy_context = await strategy_context_for_next_session(session, profile, target_groups)

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
    if recent_skipped_ids:
        without_skipped = [e for e in candidates if e.id not in recent_skipped_ids]
        if len(without_skipped) >= 3:
            candidates = without_skipped
    if avoid_exercise_codes:
        without_avoided = [e for e in candidates if e.code not in avoid_exercise_codes]
        if len(without_avoided) >= 3:
            candidates = without_avoided

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
        if prefer_exercise_codes:
            ranked = sorted(ranked, key=lambda ex: ex.code in prefer_exercise_codes, reverse=True)
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
    sets_count = max(
        1,
        round((params["sets"] + mod["sets"]) * strategy_context.volume_factor)
        + int(review_adjustment["sets_delta"])
        + int(health_adjustment["sets_delta"]),
    )
    rest_secs = round(
        params["rest"]
        * mod["rest_factor"]
        * strategy_context.rest_factor
        * float(review_adjustment["rest_factor"])
        * float(health_adjustment["rest_factor"])
    )
    if modifier == "hard":
        rest_secs = max(rest_secs, 120)
    time_per_ex = sets_count * (45 + rest_secs) / 60
    max_ex = max(3, int((profile.preferred_duration_min or 45) / time_per_ex))
    if last_review and (last_review.skipped_exercise_ids or []):
        max_ex = max(3, max_ex - 1)
    selected = selected[:max_ex]

    # Assign volume and save
    from services.progression import calculate_next_weight
    result_list = []
    for idx, ex in enumerate(selected):
        reps_min, reps_max = _target_reps_range(goal, modifier, ex.exercise_type)
        target_reps = random.randint(reps_min, reps_max)
        last_w = await _get_last_weight(session, profile.user_id, ex.id)
        start_weight = _starting_weight_for(ex, equipment_codes_by_id)
        calibrated_weight = None if last_w is not None else await calibrated_start_weight(
            session, profile.user_id, ex, target_reps
        )
        if start_weight == 0.0 and last_w is None and calibrated_weight is None:
            weight = 0.0
        else:
            if calibrated_weight is not None and last_w is None:
                weight = calibrated_weight
            else:
                weight = calculate_next_weight(
                    last_weight_kg=last_w if last_w is not None else start_weight,
                    last_reps_done=target_reps, target_reps=target_reps,
                    last_rpe=None, exercise_type=ex.exercise_type.value, difficulty_modifier=modifier,
                )
            muscle_code = next((code for code, mg_id in muscle_groups if mg_id == ex.primary_muscle_group_id), "")
            muscle_factor = 1.0
            if muscle_code in reduce_muscle_groups:
                muscle_factor *= 0.9
            if muscle_code in focus_muscle_groups and muscle_code not in reduce_muscle_groups:
                muscle_factor *= 1.03
            weight *= (
                mod["weight_pct"]
                * strategy_context.intensity_factor
                * float(review_adjustment["weight_factor"])
                * float(health_adjustment["weight_factor"])
                * muscle_factor
            )
            weight = round(weight, 2)

        se = SessionExercise(
            session_id=workout_session_id, exercise_id=ex.id, order_index=idx,
            target_sets=sets_count, target_reps=target_reps, target_weight_kg=weight, rest_seconds=rest_secs,
        )
        session.add(se)
        result_list.append((se, ex))

    ws = await session.get(WorkoutSession, workout_session_id)
    if ws:
        ws.plan_id = strategy_context.plan.id
        ws.notes = f"rot:{rotation_idx};{strategy_context.note}"
    await session.flush()
    return result_list
