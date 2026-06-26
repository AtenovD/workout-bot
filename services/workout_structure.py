"""Workout presentation and target-set structure."""

from dataclasses import dataclass

from models.exercise import Exercise, ExerciseType, EquipmentCategory
from models.profile import Goal
from models.workout import SessionExercise


@dataclass(frozen=True)
class SetTarget:
    set_number: int
    reps: int
    weight_kg: float
    label: str


@dataclass(frozen=True)
class StructuredExercise:
    session_exercise: SessionExercise
    exercise: Exercise
    block: str
    effort: str
    warmups: list[SetTarget]


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


def _round_weight(weight: float) -> float:
    return max(0.0, round(weight / 2.5) * 2.5)


def warmup_targets_for(se: SessionExercise, ex: Exercise, modifier: str) -> list[SetTarget]:
    """Return logged warm-up sets before the working sets.

    Warm-ups are intentionally attached to the exercise instead of stored as
    extra SessionExercise rows, so summaries and progression can ignore them
    through ExerciseSet.is_warmup.
    """

    weight = float(se.target_weight_kg or 0)
    if weight <= 0 or not _is_weighted(ex):
        return []

    index = int(se.order_index or 0)
    is_compound = ex.exercise_type == ExerciseType.compound

    if is_compound:
        if modifier == "hard":
            scheme = [(10, 0.40, "разогрев"), (5, 0.60, "подводящий"), (3, 0.75, "тяжёлый подводящий")]
        elif modifier == "light":
            scheme = [(8, 0.45, "разогрев")]
        else:
            scheme = [(8, 0.45, "разогрев"), (4, 0.65, "подводящий")]

        if index > 1:
            scheme = scheme[-1:]
    elif modifier == "hard":
        scheme = [(12, 0.50, "памп-разминка")]
    else:
        scheme = []

    return [
        SetTarget(set_number=i, reps=reps, weight_kg=_round_weight(weight * ratio), label=label)
        for i, (reps, ratio, label) in enumerate(scheme, start=1)
        if _round_weight(weight * ratio) > 0
    ]


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
        return "почти в отказ, но техника чистая"
    if modifier == "light":
        return "RPE 6-7, без отказа"
    return "RPE 7-8, 1-2 повтора в запасе"


def _format_weight(weight: float) -> str:
    return f"{weight:g} кг"


def _format_work_sets(se: SessionExercise) -> str:
    weight = float(se.target_weight_kg or 0)
    weight_text = f" · {_format_weight(weight)}" if weight > 0 else ""
    return f"{se.target_sets}×{se.target_reps}{weight_text}"


def _format_warmup_summary(targets: list[SetTarget]) -> str:
    return ", ".join(f"{target.reps}×{_format_weight(target.weight_kg)}" for target in targets)


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
            warmups=warmup_targets_for(se, ex, modifier),
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
    warmup_items = [item for item in structured if item.warmups]

    lines = [
        f"🏋️ <b>{MODIFIER_TITLES.get(modifier, '⚪ Рабочая')} тренировка</b>",
        f"Цель: <b>{GOAL_TITLES.get(goal, 'силовая работа')}</b> · Время: <b>~{total_time_min} мин</b>",
        "",
        "<b>Перед рабочими весами</b>",
        "1. 5-7 минут лёгкого кардио: дорожка, вело или эллипс.",
        "2. Суставная разминка: плечи, локти, таз, колени, голеностоп.",
        "3. Активация: 1-2 лёгких подхода на мышцы первой базы.",
    ]

    if warmup_items:
        lines.append("4. Подводящие подходы в боте:")
        for item in warmup_items[:3]:
            lines.append(f"   • {item.exercise.name_ru}: {_format_warmup_summary(item.warmups)}")
    else:
        lines.append("4. Для упражнений без веса держи первый подход спокойным, без отказа.")

    lines.extend([
        "",
        "<b>План на сегодня</b>",
        "Сначала база, потом объём, затем изоляция. В тяжёлый день не гонимся за красивыми цифрами ценой техники.",
        "",
    ])

    for block in BLOCK_ORDER:
        items = [item for item in structured if item.block == block]
        if not items:
            continue
        lines.append(f"<b>{block}</b>")
        for item in items:
            lines.append(f"• {item.exercise.name_ru}: {_format_work_sets(item.session_exercise)}")
        lines.append("")

    lines.append("Ориентир: последний рабочий повтор тяжёлый, но контролируемый. Если вес не твой — жми «Тяжело» или «Легко» прямо в подходе.")
    return "\n".join(lines).strip()


def format_exercise_card(
    se: SessionExercise,
    ex: Exercise,
    current_set: int,
    modifier: str,
    is_warmup: bool = False,
    warmup_index: int = 1,
) -> str:
    index = int(se.order_index or 0) + 1
    structured = StructuredExercise(
        session_exercise=se,
        exercise=ex,
        block=_block_for(se, ex, index),
        effort=_effort_for(modifier, ex),
        warmups=warmup_targets_for(se, ex, modifier),
    )

    if is_warmup and structured.warmups:
        target = structured.warmups[min(max(warmup_index, 1), len(structured.warmups)) - 1]
        return (
            f"<b>{ex.name_ru}</b>\n"
            f"{structured.block} · разминка перед рабочими весами\n"
            f"Разминочный подход {target.set_number} из {len(structured.warmups)} · "
            f"{target.reps} повт. · {_format_weight(target.weight_kg)}\n"
            f"Темп спокойный: разогреть движение, не утомиться."
        )

    weight = float(se.target_weight_kg or 0)
    weight_text = f" · {_format_weight(weight)}" if weight > 0 else ""
    return (
        f"<b>{ex.name_ru}</b>\n"
        f"{structured.block} · {structured.effort}\n"
        f"Рабочий подход {current_set} из {se.target_sets} · "
        f"{se.target_reps} повт.{weight_text}"
    )
