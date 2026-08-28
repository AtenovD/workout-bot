"""
Progression service — calculates next workout weight based on past performance.
Uses a simple linear periodization model with RPE adjustments.
"""
# Weight step per exercise type
WEIGHT_STEP = {
    "compound": 2.5,
    "isolation": 1.25,
    "cardio": 0.0,
    "mobility": 0.0,
}

# Modifier multipliers applied BEFORE progression
MODIFIER_PCTS = {
    "light": 0.85,
    "normal": 1.0,
    "hard": 1.1,
}


def calculate_next_weight(
    last_weight_kg: float,
    last_reps_done: int,
    target_reps: int,
    last_rpe: int | None,
    exercise_type: str,
    difficulty_modifier: str = "normal",
) -> float:
    """
    Returns the recommended weight for the next session.

    Logic:
    1. If reps_done >= target_reps → progress by WEIGHT_STEP
    2. If reps_done < target_reps → keep weight
    3. RPE adjustments: RPE <= 6 → deload -10%, RPE >= 9 → no progress
    4. Modifier multiplier applied at the end (handled by workout_generator)
    """
    step = WEIGHT_STEP.get(exercise_type, 2.5)

    # Core progression rule
    if last_reps_done >= target_reps:
        next_weight = last_weight_kg + step
    else:
        next_weight = last_weight_kg

    # RPE override
    if last_rpe is not None:
        if last_rpe <= 6:
            next_weight = last_weight_kg * 0.9  # deload
        elif last_rpe >= 9:
            next_weight = last_weight_kg * 0.9  # too hard, deload

    # Round to nearest 0.5
    next_weight = round(next_weight * 2) / 2

    return max(0.0, next_weight)


def detect_plateau(weights: list[float], rpes: list[int | None] | None = None) -> bool:
    """Return True when recent weights are flat and effort is not trending down."""
    if len(weights) < 3:
        return False
    if len(set(weights[-3:])) != 1:
        return False
    recent_rpes = [r for r in (rpes or [])[-3:] if r is not None]
    return not recent_rpes or min(recent_rpes) >= 7


def estimate_1rm(weight_kg: float, reps: int) -> float:
    """Epley formula: 1RM = weight * (1 + reps / 30)"""
    if reps == 1:
        return weight_kg
    return round(weight_kg * (1 + reps / 30), 2)
