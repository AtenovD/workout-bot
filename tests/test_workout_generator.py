from types import SimpleNamespace

from models.exercise import EquipmentCategory, ExerciseType
from models.profile import Goal
from services.workout_generator import (
    _combine_review_adjustments,
    _combine_health_adjustments,
    _exercise_score,
    _is_excluded,
    _is_equipment_available,
    _rank_pool,
    _resolve_muscle_groups,
    _starting_weight_for,
    _target_reps_range,
)
from services.training_strategy import format_strategy_note_title, parse_strategy_note


def _exercise(
    code,
    equipment_id,
    category,
    exercise_type=ExerciseType.compound,
    difficulty=3,
):
    return SimpleNamespace(
        id=hash(code),
        code=code,
        name_ru=code,
        name_en=code,
        required_equipment_id=equipment_id,
        equipment_category=category,
        exercise_type=exercise_type,
        difficulty=difficulty,
    )


def test_detailed_and_legacy_muscle_codes_are_supported():
    available = {
        "chest": 1,
        "lats": 2,
        "middle_back": 3,
        "quadriceps": 4,
        "hamstrings": 5,
        "front_delts": 6,
        "abs": 7,
    }

    resolved = _resolve_muscle_groups(["back", "legs", "shoulders", "core"], available)

    assert resolved == [
        ("lats", 2),
        ("middle_back", 3),
        ("quadriceps", 4),
        ("hamstrings", 5),
        ("front_delts", 6),
        ("abs", 7),
    ]


def test_unselected_equipment_is_not_available():
    dumbbell = _exercise("db_press", 10, EquipmentCategory.portable)
    trx = _exercise("trx_row", 20, EquipmentCategory.portable)
    bodyweight = _exercise("pushup", 30, EquipmentCategory.none)

    assert _is_equipment_available(dumbbell, {10}, {"dumbbell"}) is True
    assert _is_equipment_available(trx, {10}, {"dumbbell"}) is False
    assert _is_equipment_available(bodyweight, {10}, {"dumbbell"}) is True


def test_trx_code_is_blocked_when_seeded_as_bodyweight_without_trx_selected():
    trx_pushup = _exercise("trx_pushup", 30, EquipmentCategory.none)

    assert _is_equipment_available(trx_pushup, {30}, {"bodyweight"}) is False
    assert _is_equipment_available(trx_pushup, {20, 30}, {"trx", "bodyweight"}) is True


def test_hard_workout_prefers_selected_weights_over_bodyweight():
    dumbbell = _exercise("db_bench_press", 10, EquipmentCategory.portable, difficulty=3)
    pushup = _exercise("pushup", 30, EquipmentCategory.none, difficulty=5)

    ranked = _rank_pool([pushup, dumbbell], {10}, "hard", has_weighted_equipment=True)

    assert ranked[0].code == "db_bench_press"
    assert _exercise_score(dumbbell, {10}, "hard", True) > _exercise_score(pushup, {10}, "hard", True)


def test_hard_workout_uses_strength_rep_ranges():
    assert _target_reps_range(Goal.weight_loss, "hard", ExerciseType.compound) == (5, 8)
    assert _target_reps_range(Goal.mass_gain, "hard", ExerciseType.isolation) == (8, 12)
    assert _target_reps_range(Goal.weight_loss, "normal", ExerciseType.compound) == (12, 18)


def test_bodyweight_equipment_keeps_zero_starting_weight():
    pullup = _exercise("pullup", 5, EquipmentCategory.portable)
    dumbbell = _exercise("db_press", 10, EquipmentCategory.portable)

    assert _starting_weight_for(pullup, {5: "pullup_bar"}) == 0.0
    assert _starting_weight_for(dumbbell, {10: "dumbbell"}) > 0.0


def test_review_feedback_adjusts_future_workout_load():
    review = SimpleNamespace(intensity_feedback="easier", pain_feedback="discomfort")

    adjustment = _combine_review_adjustments(review)

    assert adjustment["sets_delta"] == -2
    assert round(adjustment["weight_factor"], 3) == 0.81
    assert round(adjustment["rest_factor"], 3) == 1.265


def test_no_review_keeps_neutral_workout_load():
    assert _combine_review_adjustments(None) == {
        "sets_delta": 0,
        "weight_factor": 1.0,
        "rest_factor": 1.0,
        "avoid_exercise_codes": [],
        "prefer_exercise_codes": [],
        "reduce_muscle_groups": [],
        "focus_muscle_groups": [],
    }


def test_ai_adjustment_is_merged_and_clamped():
    review = SimpleNamespace(
        intensity_feedback="harder",
        pain_feedback="none",
        ai_adjustment={
            "sets_delta": 4,
            "weight_factor": 1.5,
            "rest_factor": 0.2,
            "avoid_exercise_codes": ["overhead_press"],
            "focus_muscle_groups": ["chest"],
        },
    )

    adjustment = _combine_review_adjustments(review)

    assert adjustment["sets_delta"] == 1
    assert adjustment["weight_factor"] == 1.1
    assert adjustment["rest_factor"] == 0.85
    assert adjustment["avoid_exercise_codes"] == ["overhead_press"]
    assert adjustment["focus_muscle_groups"] == ["chest"]


def test_hernia_flags_exclude_high_pressure_exercises():
    assert _is_excluded("deadlift", ["hiatal_hernia"]) is True
    assert _is_excluded("leg_press_ex", ["inguinal_hernia"]) is True
    assert _is_excluded("ab_wheel", ["umbilical_hernia"]) is True
    assert _is_excluded("cable_crunch", ["hernia"]) is True
    assert _is_excluded("db_bench_press", ["hiatal_hernia"]) is False


def test_health_flags_reduce_load_and_add_rest():
    adjustment = _combine_health_adjustments(["hiatal_hernia", "hypertension"])

    assert adjustment["sets_delta"] == -2
    assert adjustment["weight_factor"] < 0.8
    assert adjustment["rest_factor"] > 1.3


def test_strategy_notes_are_parseable_with_rotation_prefix():
    note = "rot:4;plan:9;week:3;phase:progression;session:1;focus:chest,back"

    parsed = parse_strategy_note(note)

    assert parsed["rot"] == "4"
    assert parsed["week"] == "3"
    assert parsed["phase"] == "progression"
    assert format_strategy_note_title(note) == "Неделя прогрессии · неделя 3/6"
