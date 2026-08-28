"""Workout presentation and target-set structure."""

from dataclasses import dataclass

from models.exercise import Exercise, ExerciseType, EquipmentCategory
from models.profile import Goal, SplitType, TrainingStructure
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

MODIFIER_TITLES_EN = {
    "light": "🟢 Light",
    "normal": "⚪ Normal",
    "hard": "🔴 Heavy",
}

GOAL_TITLES = {
    Goal.mass_gain: "масса",
    Goal.weight_loss: "сушка/расход",
    Goal.maintenance: "поддержание",
    Goal.cardio: "выносливость",
}

GOAL_TITLES_EN = {
    Goal.mass_gain: "muscle gain",
    Goal.weight_loss: "fat loss",
    Goal.maintenance: "maintenance",
    Goal.cardio: "endurance",
}

BLOCK_ORDER = ["Силовой блок", "Объёмный блок", "Изоляция", "Кор и контроль"]

BLOCK_TITLES_EN = {
    "Силовой блок": "Strength block",
    "Объёмный блок": "Volume block",
    "Изоляция": "Isolation",
    "Кор и контроль": "Core and control",
}

STRUCTURE_TITLES = {
    TrainingStructure.fullbody: "Фулбади",
    TrainingStructure.split: "Сплит",
}

SPLIT_TITLES = {
    SplitType.upper_lower: "Верх/низ",
    SplitType.push_pull_legs: "Push/Pull/Legs",
    SplitType.bro_split: "Классический сплит",
}

SPLIT_TITLES_EN = {
    SplitType.upper_lower: "Upper/lower",
    SplitType.push_pull_legs: "Push/Pull/Legs",
    SplitType.bro_split: "Classic split",
}


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


def _effort_for(modifier: str, ex: Exercise, lang: str = "ru") -> str:
    if modifier == "hard":
        if ex.exercise_type == ExerciseType.compound:
            return "RPE 8-9, 1 rep in reserve" if lang == "en" else "RPE 8-9, 1 повтор в запасе"
        return "near failure, clean technique" if lang == "en" else "почти в отказ, но техника чистая"
    if modifier == "light":
        return "RPE 6-7, no failure" if lang == "en" else "RPE 6-7, без отказа"
    return "RPE 7-8, 1-2 reps in reserve" if lang == "en" else "RPE 7-8, 1-2 повтора в запасе"


def _format_weight(weight: float, lang: str = "ru") -> str:
    return f"{weight:g} kg" if lang == "en" else f"{weight:g} кг"


def _format_work_sets(se: SessionExercise, lang: str = "ru") -> str:
    weight = float(se.target_weight_kg or 0)
    weight_text = f" · {_format_weight(weight, lang)}" if weight > 0 else ""
    return f"{se.target_sets}x{se.target_reps}{weight_text}"


def _format_warmup_summary(targets: list[SetTarget], lang: str = "ru") -> str:
    return ", ".join(f"{target.reps}x{_format_weight(target.weight_kg, lang)}" for target in targets)


def _training_format_title(
    training_structure: TrainingStructure | str | None,
    split_type: SplitType | str | None,
    lang: str = "ru",
) -> str:
    if isinstance(training_structure, str):
        training_structure = TrainingStructure(training_structure) if training_structure in TrainingStructure._value2member_map_ else None
    if isinstance(split_type, str):
        split_type = SplitType(split_type) if split_type in SplitType._value2member_map_ else None

    if training_structure == TrainingStructure.fullbody:
        return "Full body" if lang == "en" else "Фулбади"
    if training_structure == TrainingStructure.split:
        if lang == "en":
            return f"Split · {SPLIT_TITLES_EN.get(split_type, 'muscle groups')}"
        return f"Сплит · {SPLIT_TITLES.get(split_type, 'по группам мышц')}"
    return "Personal plan" if lang == "en" else "Персональный план"


def _muscle_label(ex: Exercise, muscle_names_by_id: dict[int, str] | None, lang: str = "ru") -> str:
    fallback = "muscle not set" if lang == "en" else "группа не указана"
    if not muscle_names_by_id or not ex.primary_muscle_group_id:
        return fallback
    return muscle_names_by_id.get(ex.primary_muscle_group_id, fallback)


def _exercise_name(ex: Exercise, lang: str = "ru") -> str:
    if lang == "en":
        return ex.name_en or ex.name_ru or ex.code
    return ex.name_ru or ex.name_en or ex.code


def _block_title(block: str, lang: str = "ru") -> str:
    return BLOCK_TITLES_EN.get(block, block) if lang == "en" else block


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
    training_structure: TrainingStructure | str | None = None,
    split_type: SplitType | str | None = None,
    muscle_names_by_id: dict[int, str] | None = None,
    strategy_title: str | None = None,
    lang: str = "ru",
) -> str:
    structured = structure_workout(exercises, modifier)
    warmup_items = [item for item in structured if item.warmups]

    if lang == "en":
        lines = [
            f"🏋️ <b>{MODIFIER_TITLES_EN.get(modifier, '⚪ Normal')} workout</b>",
            f"Goal: <b>{GOAL_TITLES_EN.get(goal, 'strength work')}</b> · Time: <b>~{total_time_min} min</b>",
            f"Format: <b>{_training_format_title(training_structure, split_type, lang)}</b>",
            "",
            "<b>Before working sets</b>",
            "1. 5-7 min easy cardio: treadmill, bike, or elliptical.",
            "2. Joint warm-up: shoulders, elbows, hips, knees, ankles.",
            "3. Activation: 1-2 light sets for the first main movement.",
        ]
        if strategy_title:
            lines.insert(3, f"Strategy: <b>{strategy_title}</b>")
        if warmup_items:
            lines.append("4. Ramp-up sets in the bot:")
            for item in warmup_items[:3]:
                lines.append(f"   • {_exercise_name(item.exercise, lang)}: {_format_warmup_summary(item.warmups, lang)}")
        else:
            lines.append("4. For bodyweight exercises, keep the first set controlled and away from failure.")
        lines.extend([
            "",
            "<b>Today's plan</b>",
            "Main lifts first, then volume, then isolation. On heavy days, technique beats pretty numbers.",
            "",
        ])
    else:
        lines = [
            f"🏋️ <b>{MODIFIER_TITLES.get(modifier, '⚪ Рабочая')} тренировка</b>",
            f"Цель: <b>{GOAL_TITLES.get(goal, 'силовая работа')}</b> · Время: <b>~{total_time_min} мин</b>",
            f"Формат: <b>{_training_format_title(training_structure, split_type, lang)}</b>",
            "",
            "<b>Перед рабочими весами</b>",
            "1. 5-7 минут лёгкого кардио: дорожка, вело или эллипс.",
            "2. Суставная разминка: плечи, локти, таз, колени, голеностоп.",
            "3. Активация: 1-2 лёгких подхода на мышцы первой базы.",
        ]
        if strategy_title:
            lines.insert(3, f"Стратегия: <b>{strategy_title}</b>")
        if warmup_items:
            lines.append("4. Подводящие подходы в боте:")
            for item in warmup_items[:3]:
                lines.append(f"   • {_exercise_name(item.exercise, lang)}: {_format_warmup_summary(item.warmups, lang)}")
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
        lines.append(f"<b>{_block_title(block, lang)}</b>")
        for item in items:
            muscle = _muscle_label(item.exercise, muscle_names_by_id, lang)
            lines.append(f"• {_exercise_name(item.exercise, lang)} · <i>{muscle}</i>: {_format_work_sets(item.session_exercise, lang)}")
        lines.append("")

    if lang == "en":
        lines.append("Target feel: the last working rep should be hard but controlled. If the load is wrong, tap Hard or Easy during the set.")
    else:
        lines.append("Ориентир: последний рабочий повтор тяжёлый, но контролируемый. Если вес не твой — жми «Тяжело» или «Легко» прямо в подходе.")
    return "\n".join(lines).strip()


def format_exercise_card(
    se: SessionExercise,
    ex: Exercise,
    current_set: int,
    modifier: str,
    is_warmup: bool = False,
    warmup_index: int = 1,
    muscle_names_by_id: dict[int, str] | None = None,
    lang: str = "ru",
) -> str:
    index = int(se.order_index or 0) + 1
    structured = StructuredExercise(
        session_exercise=se,
        exercise=ex,
        block=_block_for(se, ex, index),
        effort=_effort_for(modifier, ex, lang),
        warmups=warmup_targets_for(se, ex, modifier),
    )

    if is_warmup and structured.warmups:
        target = structured.warmups[min(max(warmup_index, 1), len(structured.warmups)) - 1]
        if lang == "en":
            return (
                f"<b>{_exercise_name(ex, lang)}</b>\n"
                f"{_block_title(structured.block, lang)} · {_muscle_label(ex, muscle_names_by_id, lang)} · warm-up before working sets\n"
                f"Warm-up set {target.set_number} of {len(structured.warmups)} · "
                f"{target.reps} reps · {_format_weight(target.weight_kg, lang)}\n"
                "Keep the tempo calm: warm up the movement, do not fatigue yourself."
            )
        return (
            f"<b>{_exercise_name(ex, lang)}</b>\n"
            f"{structured.block} · {_muscle_label(ex, muscle_names_by_id, lang)} · разминка перед рабочими весами\n"
            f"Разминочный подход {target.set_number} из {len(structured.warmups)} · "
            f"{target.reps} повт. · {_format_weight(target.weight_kg, lang)}\n"
            f"Темп спокойный: разогреть движение, не утомиться."
        )

    weight = float(se.target_weight_kg or 0)
    weight_text = f" · {_format_weight(weight, lang)}" if weight > 0 else ""
    if lang == "en":
        return (
            f"<b>{_exercise_name(ex, lang)}</b>\n"
            f"{_block_title(structured.block, lang)} · {_muscle_label(ex, muscle_names_by_id, lang)} · {structured.effort}\n"
            f"Working set {current_set} of {se.target_sets} · "
            f"{se.target_reps} reps{weight_text}"
        )
    return (
        f"<b>{_exercise_name(ex, lang)}</b>\n"
        f"{structured.block} · {_muscle_label(ex, muscle_names_by_id, lang)} · {structured.effort}\n"
        f"Рабочий подход {current_set} из {se.target_sets} · "
        f"{se.target_reps} повт.{weight_text}"
    )
