"""Workout presentation structure.

The generator stores a compact exercise list in the DB. This module turns that
list into a coach-like plan for Telegram: warm-up guidance, training blocks,
effort target, and compact exercise cards.
"""

from dataclasses import dataclass

from models.exercise import Exercise, ExerciseType, EquipmentCategory
from models.profile import Goal
from models.workout import SessionExercise


@dataclass(frozen=True)
class StructuredExercise:
    session_exercise: SessionExercise
    exercise: Exercise
    block: str
    effort: str
    warmup: str | None


MODIFIER_TITLES = {
    "light": "🟢 Облегчённая",
    "normal": "⚪ Рабочая",
    "hard": "🔴 Тяжёлая",
}

GOAL_TITLES = {
    Goal.mass_gain: "масса",
    Goal.weight_loss: "сушка/расход",
    Goal.maintenance: "поддержание",
    Goal.cardio: "выносливость",
}

BLOCK_ORDER = ["Силовой блок", "Объёмный блок", "Изоляция", "Кор и контроль"]


def _is_weighted(ex: Exercise) -> bool:
    return ex.equipment_category != EquipmentCategory.none


def _warmup_hint(se: SessionExercise, ex: Exercise, index: int) -> str | None:
    weight = float(se.target_weight_kg or 0)
    if index > 1 or weight <= 0 or ex.exercise_type != ExerciseType.compound or not _is_weighted(ex):
        return None
    first = max(0, round(weight * 0.45 / 2.5) * 2.5)
    second = max(0, round(weight * 0.7 / 2.5) * 2.5)
    if second <= first:
        return f"разминка: 1 лёгкий подход перед рабочими"
    return f"разминка: {first:g} кг × 8, {second:g} кг × 4"


def _block_for(se: SessionExercise, ex: Exercise, index: int) -> str:
    code = ex.code or ""
    if index <= 2 and ex.exercise_type == ExerciseType.compound:
        return "Силовой блок"
    if ex.exercise_type == ExerciseType.compound:
        return "Объёмный блок"
    if any(part in code for part in ("crunch", "plank", "abs", "leg_raise", "woodchop")):
        return "Кор и контроль"
    return "Изоляция"


def _effort_for(modifier: str, ex: Exercise) -> str:
    if modifier == "hard":
        if ex.exercise_type == ExerciseType.compound:
            return "RPE 8-9, 1 повтор в запасе"
        return "почти в отказ, чистая техника"
    if modifier == "light":
        return "RPE 6-7, без отказа"
    return "RPE 7-8, 1-2 повтора в запасе"


def structure_workout(
    exercises: list[tuple[SessionExercise, Exercise]],
    modifier: str,
) -> list[StructuredExercise]:
    return [
        StructuredExercise(
            session_exercise=se,
            exercise=ex,
            block=_block_for(se, ex, idx),
            effort=_effort_for(modifier, ex),
            warmup=_warmup_hint(se, ex, idx),
        )
        for idx, (se, ex) in enumerate(exercises, start=1)
    ]


def format_workout_overview(
    exercises: list[tuple[SessionExercise, Exercise]],
    modifier: str,
    goal: Goal | None,
    total_time_min: int,
) -> str:
    structured = structure_workout(exercises, modifier)
    lines = [
        f"🏋️ <b>{MODIFIER_TITLES.get(modifier, '⚪ Рабочая')} тренировка</b>",
        f"Цель: <b>{GOAL_TITLES.get(goal, 'силовая работа')}</b> · Время: <b>~{total_time_min} мин</b>",
        "",
        "План на сегодня:",
        "1. Разогрев: 5-7 мин + суставная разминка",
        "2. Тяжёлые движения: сначала база, пока свежий",
        "3. Объём и изоляция: добираем мышцы без хаоса",
        "",
    ]
    for block in BLOCK_ORDER:
        items = [item for item in structured if item.block == block]
        if not items:
            continue
        lines.append(f"<b>{block}</b>")
        for item in items:
            se = item.session_exercise
            ex = item.exercise
            weight = float(se.target_weight_kg or 0)
            weight_text = f" · {weight:g} кг" if weight > 0 else ""
            lines.append(f"• {ex.name_ru}: {se.target_sets}×{se.target_reps}{weight_text}")
            if item.warmup:
                lines.append(f"  ↳ {item.warmup}")
        lines.append("")
    lines.append("В подходах ориентир: техника чистая, последний повтор тяжёлый, но контролируемый.")
    return "\n".join(lines).strip()


def format_exercise_card(
    se: SessionExercise,
    ex: Exercise,
    current_set: int,
    modifier: str,
) -> str:
    index = int(se.order_index or 0) + 1
    structured = StructuredExercise(
        session_exercise=se,
        exercise=ex,
        block=_block_for(se, ex, index),
        effort=_effort_for(modifier, ex),
        warmup=_warmup_hint(se, ex, index),
    )
    weight = float(se.target_weight_kg or 0)
    weight_text = f" · {weight:g} кг" if weight > 0 else ""
    warmup = f"\n{structured.warmup}" if structured.warmup and current_set == 1 else ""
    return (
        f"<b>{ex.name_ru}</b>\n"
        f"{structured.block} · {structured.effort}\n"
        f"Рабочий подход {current_set} из {se.target_sets} · "
        f"{se.target_reps} повт.{weight_text}"
        f"{warmup}"
    )
