"""
Workout Generator Service — the core of the bot.
Generates a personalized workout session based on user profile, equipment, and history.
"""
from dataclasses import dataclass, field
from typing import Optional
from models.profile import Goal, ExperienceLevel, TrainingStructure
from models.exercise import EquipmentCategory, ExerciseType


@dataclass
class ExercisePlan:
    exercise_id: int
    exercise_name: str
    target_sets: int
    target_reps: int
    target_weight_kg: Optional[float]
    rest_seconds: int
    order_index: int


@dataclass
class GeneratedWorkout:
    exercises: list[ExercisePlan] = field(default_factory=list)
    estimated_duration_min: int = 45
    target_muscle_groups: list[str] = field(default_factory=list)
    total_estimated_volume: float = 0.0


# Volume parameters by goal
GOAL_PARAMS = {
    Goal.mass_gain:    {"reps": (8, 12),  "sets": (3, 4), "rest": 105},
    Goal.weight_loss:  {"reps": (12, 18), "sets": 3,      "rest": 45},
    Goal.maintenance:  {"reps": (10, 12), "sets": 3,      "rest": 75},
    Goal.cardio:       {"reps": (15, 20), "sets": 3,      "rest": 30},
}

DIFFICULTY_MODIFIERS = {
    "light": {"sets_delta": -1, "weight_pct": 0.85, "rest_factor": 1.3},
    "normal": {"sets_delta": 0,  "weight_pct": 1.0,  "rest_factor": 1.0},
    "hard":  {"sets_delta": 1,  "weight_pct": 1.1,  "rest_factor": 0.8},
}

# Health flags → exercises to exclude (by code prefixes)
HEALTH_EXCLUSIONS = {
    "lower_back_pain":  ["deadlift", "good_morning", "hyperextension"],
    "knee_injury":      ["squat_deep", "lunge_full", "leg_press_full"],
    "shoulder_issue":   ["overhead_press_heavy", "upright_row"],
    "hernia":           ["deadlift", "heavy_squat", "leg_press"],
}


def get_target_muscle_groups(
    structure: TrainingStructure,
    split_type: Optional[str],
    rotation_index: int,
) -> list[str]:
    """Determine which muscle groups to train today."""
    if structure == TrainingStructure.fullbody:
        return ["chest", "back", "legs", "shoulders", "biceps", "triceps", "core"]

    rotations = {
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
            ["chest"], ["back"], ["shoulders"], ["legs"], ["arms"],
        ],
    }

    if split_type and split_type in rotations:
        days = rotations[split_type]
        return days[rotation_index % len(days)]

    return ["chest", "back", "legs", "shoulders", "biceps", "triceps", "core"]


def estimate_duration(exercises: list[ExercisePlan]) -> int:
    """Estimate workout duration in minutes."""
    warmup = 5
    cooldown = 5
    total = warmup + cooldown
    for ex in exercises:
        set_time = 45  # seconds per set
        total += ex.target_sets * (set_time + ex.rest_seconds) / 60
    return round(total)


def apply_modifier(sets: int, weight: float, rest: int, modifier: str) -> tuple[int, float, int]:
    mod = DIFFICULTY_MODIFIERS.get(modifier, DIFFICULTY_MODIFIERS["normal"])
    new_sets = max(1, sets + mod["sets_delta"])
    new_weight = round(weight * mod["weight_pct"], 2)
    new_rest = round(rest * mod["rest_factor"])
    return new_sets, new_weight, new_rest
