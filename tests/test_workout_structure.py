from types import SimpleNamespace

from models.exercise import EquipmentCategory, ExerciseType
from models.profile import Goal
from services.workout_structure import (
    format_exercise_card,
    format_workout_overview,
    structure_workout,
    warmup_targets_for,
)


def _exercise(code, name, exercise_type, category=EquipmentCategory.stationary):
    return SimpleNamespace(
        code=code,
        name_ru=name,
        name_en=name,
        exercise_type=exercise_type,
        equipment_category=category,
    )


def _session_exercise(order, sets=4, reps=6, weight=80):
    return SimpleNamespace(
        order_index=order,
        target_sets=sets,
        target_reps=reps,
        target_weight_kg=weight,
        rest_seconds=120,
    )


def test_hard_compound_gets_full_warmup_ramp():
    se = _session_exercise(0, sets=4, reps=6, weight=100)
    ex = _exercise("bench_press", "Жим лёжа", ExerciseType.compound)

    targets = warmup_targets_for(se, ex, "hard")

    assert [(t.reps, t.weight_kg) for t in targets] == [(10, 40.0), (5, 60.0), (3, 75.0)]


def test_workout_overview_is_structured_into_coach_blocks():
    exercises = [
        (_session_exercise(0), _exercise("bench_press", "Жим лёжа", ExerciseType.compound)),
        (_session_exercise(1), _exercise("barbell_row", "Тяга штанги", ExerciseType.compound)),
        (_session_exercise(2, reps=10, weight=12), _exercise("db_flyes", "Разводка", ExerciseType.isolation)),
    ]

    text = format_workout_overview(exercises, "hard", Goal.mass_gain, 55)

    assert "Перед рабочими весами" in text
    assert "Подводящие подходы" in text
    assert "Силовой блок" in text
    assert "Изоляция" in text
    assert "RPE" not in text


def test_exercise_card_shows_warmup_phase_before_work_sets():
    se = _session_exercise(0, sets=4, reps=6, weight=100)
    ex = _exercise("bench_press", "Жим лёжа", ExerciseType.compound)

    warmup_text = format_exercise_card(se, ex, 1, "hard", is_warmup=True, warmup_index=2)
    work_text = format_exercise_card(se, ex, 1, "hard")

    assert "Разминочный подход 2 из 3" in warmup_text
    assert "5 повт. · 60 кг" in warmup_text
    assert "Рабочий подход 1 из 4" in work_text
    assert "RPE 8-9" in work_text


def test_exercise_card_omits_weight_for_bodyweight():
    se = _session_exercise(1, sets=4, reps=8, weight=0)
    ex = _exercise("pullup_wide", "Подтягивания", ExerciseType.compound, EquipmentCategory.none)

    text = format_exercise_card(se, ex, 1, "hard")

    assert "0 кг" not in text
    assert "Рабочий подход 1 из 4" in text


def test_structure_workout_keeps_block_names():
    exercises = [
        (_session_exercise(0), _exercise("bench_press", "Жим лёжа", ExerciseType.compound)),
        (_session_exercise(2, reps=10, weight=12), _exercise("db_flyes", "Разводка", ExerciseType.isolation)),
    ]

    blocks = [item.block for item in structure_workout(exercises, "normal")]

    assert blocks == ["Силовой блок", "Изоляция"]
