import pytest
from services.calibration import process_calibration, calculate_intensity
from services.progression import calculate_next_weight, detect_plateau, estimate_1rm
from services.gamification import calculate_xp, get_level_from_xp, get_title
from models.profile import Goal, ExperienceLevel


def test_calibration_beginner_always_fullbody():
    result = process_calibration(
        experience_level=ExperienceLevel.beginner,
        experience_months=0,
        age=25,
        health_flags=[],
        days_per_week=5,
        preferred_duration_min=60,
        goal=Goal.mass_gain,
    )
    from models.profile import TrainingStructure
    assert result.training_structure == TrainingStructure.fullbody


def test_intensity_with_injury():
    intensity = calculate_intensity(ExperienceLevel.advanced, 30, ["lower_back_pain"])
    assert intensity <= 3


def test_progression_increase():
    new_weight = calculate_next_weight(
        last_weight_kg=80.0, last_reps_done=10,
        target_reps=10, last_rpe=7,
        exercise_type="compound", difficulty_modifier="normal",
    )
    assert new_weight > 80.0


def test_progression_decrease():
    new_weight = calculate_next_weight(
        last_weight_kg=80.0, last_reps_done=6,
        target_reps=10, last_rpe=10,
        exercise_type="compound", difficulty_modifier="normal",
    )
    assert new_weight < 80.0


def test_1rm_estimate():
    orm = estimate_1rm(100.0, 5)
    assert 115 < orm < 120


def test_plateau_detection():
    assert detect_plateau([80, 80, 80], [7, 7, 7]) == True
    assert detect_plateau([80, 82.5, 85], [7, 7, 7]) == False


def test_xp_calculation():
    result = calculate_xp(
        total_volume_kg=3000, difficulty_modifier="hard",
        streak=7, pr_count=1, was_skipped_before=False
    )
    assert result.xp_earned > 50


def test_level_from_xp():
    assert get_level_from_xp(0) == 1
    assert get_level_from_xp(1000) > 1


def test_titles():
    assert get_title(1) == "Новичок"
    assert get_title(10) == "Атлет"
    assert get_title(50) == "Легенда"
