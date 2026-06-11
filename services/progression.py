"""
Progressive overload service: calculates recommended weights and detects plateaus.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProgressionRecommendation:
    recommended_weight_kg: float
    recommended_reps: int
    notes: str = ""


def estimate_1rm(weight_kg: float, reps: int) -> float:
    """Epley formula: 1RM = weight * (1 + reps/30)"""
    if reps == 1:
        return weight_kg
    return weight_kg * (1 + reps / 30)


def calculate_next_weight(
    last_weight_kg: float,
    last_reps_done: int,
    target_reps: int,
    last_rpe: Optional[int],
    exercise_type: str,  # "compound" or "isolation"
    difficulty_modifier: str,  # "light", "normal", "hard"
) -> float:
    """
    Progressive overload logic:
    - If last RPE <= 7 and hit target reps → increase weight
    - If last RPE >= 9 or missed reps → decrease or hold
    """
    step_compound = 2.5  # kg
    step_isolation = 1.25  # kg
    step = step_compound if exercise_type == "compound" else step_isolation

    if difficulty_modifier == "light":
        return round(last_weight_kg * 0.85, 2)
    elif difficulty_modifier == "hard":
        step *= 1.5

    if last_rpe is None:
        return last_weight_kg

    if last_reps_done >= target_reps and last_rpe <= 7:
        return round(last_weight_kg + step, 2)
    elif last_rpe >= 9 or last_reps_done < target_reps * 0.9:
        return round(max(last_weight_kg - step, 0), 2)
    else:
        return last_weight_kg


def detect_plateau(recent_weights: list[float], recent_rpes: list[int]) -> bool:
    """Detect plateau: 3+ sessions without progress and RPE stable."""
    if len(recent_weights) < 3:
        return False
    last_3 = recent_weights[-3:]
    return max(last_3) - min(last_3) < 1.25


def should_deload(total_hard_sessions: int, last_deload_session: int) -> bool:
    """Suggest deload every 4-6 weeks of hard training."""
    sessions_since_deload = total_hard_sessions - last_deload_session
    return sessions_since_deload >= 16  # ~4 weeks at 4x/week
