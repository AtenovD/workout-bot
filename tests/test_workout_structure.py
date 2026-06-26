from types import SimpleNamespace

from models.exercise import EquipmentCategory, ExerciseType
from models.profile import Goal
from services.workout_structure import format_exercise_card, format_workout_overview, structure_workout


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


def test_workout_overview_is_structured_into_coach_blocks():
    exercises = [
        (_session_exercise(0), _exercise("bench_press", "Жим лёжа", ExerciseType.compound)),
        (_session_exercise(1), _exercise("barbell_row", "Тяга штанги", ExerciseType.compound)),
        (_session_exercise(2, reps=10, weight=12), _exercise("db_flyes", "Разводка", ExerciseType.isolation)),
    ]

    text = format_workout_overview(exercises, "hard", Goal.mass_gain, 55)

    assert "План на сегодня" in text
    assert "Силовой блок" in text
    assert "Изоляция" in text
    assert "разминка:" in text
    assert "RPE" not in text


def test_exercise_card_shows_effort_and_warmup_for_first_weighted_compound():
    se = _session_exercise(0, sets=4, reps=6, weight=100)
    ex = _exercise("bench_press", "Жим лёжа", ExerciseType.compound)

    text = format_exercise_card(se, ex, 1, "hard")

    assert "Силовой блок" in text
    assert "RPE 8-9" in text
    assert "разминка:" in text


def test_exercise_card_omits_weight_for_bodyweight():
    se = _session_exercise(1, sets=4, reps=8, weight=0)
    ex = _exercise("pullup_wide", "Подтягивания", ExerciseType.compound, EquipmentCategory.portable)

    text = format_exercise_card(se, ex, 1, "hard")

    assert "0 кг" not in text
    assert "Рабочий подход 1 из 4" in text
