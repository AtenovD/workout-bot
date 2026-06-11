"""
Calibration service: processes onboarding answers → builds user profile.
"""
from dataclasses import dataclass
from models.profile import Goal, ExperienceLevel, TrainingStructure, SplitType


@dataclass
class CalibrationResult:
    intensity_level: int
    training_structure: TrainingStructure
    split_type: SplitType | None
    recommended_days_per_week: int
    recommended_duration_min: int


def calculate_intensity(
    experience_level: ExperienceLevel,
    age: int,
    health_flags: list[str],
) -> int:
    """Calculate intensity 1-5 based on experience, age, health flags."""
    base = {
        ExperienceLevel.beginner: 2,
        ExperienceLevel.intermediate: 3,
        ExperienceLevel.advanced: 4,
    }.get(experience_level, 2)

    if age >= 50:
        base = max(1, base - 1)
    elif age >= 45:
        base = max(1, base - 0.5)

    risky_flags = {"knee_injury", "lower_back_pain", "shoulder_issue", "hernia"}
    if any(f in risky_flags for f in health_flags):
        base = max(1, base - 1)

    return min(5, max(1, round(base)))


def determine_structure(
    days_per_week: int,
    experience_level: ExperienceLevel,
) -> tuple[TrainingStructure, SplitType | None]:
    """Determine training structure based on frequency and experience."""
    # Beginners always start with fullbody
    if experience_level == ExperienceLevel.beginner:
        return TrainingStructure.fullbody, None

    if days_per_week <= 3:
        return TrainingStructure.fullbody, None
    elif days_per_week == 4:
        return TrainingStructure.split, SplitType.upper_lower
    else:  # 5-6 days
        return TrainingStructure.split, SplitType.push_pull_legs


def process_calibration(
    experience_level: ExperienceLevel,
    experience_months: int,
    age: int,
    health_flags: list[str],
    days_per_week: int,
    preferred_duration_min: int,
    goal: Goal,
) -> CalibrationResult:
    intensity = calculate_intensity(experience_level, age, health_flags)
    structure, split_type = determine_structure(days_per_week, experience_level)

    return CalibrationResult(
        intensity_level=intensity,
        training_structure=structure,
        split_type=split_type,
        recommended_days_per_week=days_per_week,
        recommended_duration_min=preferred_duration_min,
    )
