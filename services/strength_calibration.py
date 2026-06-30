import re
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.calibration import CalibrationAnswer
from models.exercise import Exercise, ExerciseType
from models.personal_record import PersonalRecord
from services.progression import estimate_1rm


@dataclass(frozen=True)
class StrengthAnchor:
    key: str
    label_ru: str
    label_en: str
    codes: tuple[str, ...]
    keywords: tuple[str, ...]
    ratios: dict[str, float]


ANCHORS: tuple[StrengthAnchor, ...] = (
    StrengthAnchor(
        key="bench_press",
        label_ru="Жим лежа",
        label_en="Bench press",
        codes=("bench_press",),
        keywords=("жим лежа", "жим лёжа", "bench", "bench press"),
        ratios={
            "bench_press": 1.0,
            "bench_press_incline_barbell": 0.85,
            "bench_press_decline": 0.9,
            "close_grip_bench": 0.8,
            "db_incline_press": 0.35,
            "fly_dumbbell": 0.18,
        },
    ),
    StrengthAnchor(
        key="squat",
        label_ru="Присед",
        label_en="Squat",
        codes=("squat_barbell", "squat", "barbell_squat"),
        keywords=("присед", "squat"),
        ratios={
            "squat_barbell": 1.0,
            "squat": 1.0,
            "barbell_squat": 1.0,
            "barbell_pause_squat": 0.85,
            "smith_squat": 0.9,
            "lunge_barbell": 0.45,
            "lunge_dumbbell": 0.25,
            "bulgarian_split_squat": 0.25,
        },
    ),
    StrengthAnchor(
        key="leg_press",
        label_ru="Жим ногами",
        label_en="Leg press",
        codes=("leg_press", "leg_press_ex"),
        keywords=("жим ног", "leg press"),
        ratios={
            "leg_press": 1.0,
            "leg_press_ex": 1.0,
            "leg_extension": 0.22,
            "leg_curl_machine": 0.2,
            "seated_leg_curl": 0.2,
        },
    ),
    StrengthAnchor(
        key="deadlift",
        label_ru="Становая тяга",
        label_en="Deadlift",
        codes=("deadlift",),
        keywords=("станов", "deadlift"),
        ratios={
            "deadlift": 1.0,
            "rdl_barbell": 0.75,
            "rdl": 0.75,
            "db_romanian_deadlift": 0.28,
        },
    ),
    StrengthAnchor(
        key="row",
        label_ru="Тяга на спину",
        label_en="Back row",
        codes=("row_cable_seated", "seated_cable_row", "row_dumbbell_single", "tbar_row"),
        keywords=("тяга на спину", "горизонтальная тяга", "тяга блока", "row", "seated row"),
        ratios={
            "row_cable_seated": 1.0,
            "seated_cable_row": 1.0,
            "tbar_row": 0.9,
            "row_dumbbell_single": 0.32,
            "lat_pulldown": 0.85,
            "lat_pulldown_wide": 0.85,
            "lat_pulldown_close": 0.85,
        },
    ),
    StrengthAnchor(
        key="overhead_press",
        label_ru="Жим над головой",
        label_en="Overhead press",
        codes=("ohp_barbell", "overhead_press"),
        keywords=("жим стоя", "жим над головой", "ohp", "overhead", "military"),
        ratios={
            "ohp_barbell": 1.0,
            "overhead_press": 1.0,
            "db_shoulder_press": 0.35,
            "ohp_dumbbell_seated": 0.35,
            "arnold_press": 0.3,
            "lateral_raise": 0.16,
            "lateral_raises": 0.16,
        },
    ),
)


def strength_calibration_help(lang: str = "ru") -> str:
    if lang == "en":
        return (
            "First workout + load calibration\n\n"
            "If you know your working weights, send a few lines now. I will convert them into estimated 1RM and use them for the first workout.\n\n"
            "Format examples:\n"
            "Bench press 80x8\n"
            "Squat 100 x 5\n"
            "Leg press 160 10\n"
            "Back row 65x10\n\n"
            "You can skip this. Then the first workout becomes diagnostic: use Hard/Easy during sets, and I will adapt the next sessions."
        )
    return (
        "Первая тренировка + калибровка весов\n\n"
        "Если знаешь свои рабочие веса, отправь несколько строк сейчас. Я переведу их в примерный 1RM и использую уже в первой тренировке.\n\n"
        "Формат:\n"
        "Жим лежа 80x8\n"
        "Присед 100 x 5\n"
        "Жим ногами 160 10\n"
        "Тяга на спину 65x10\n\n"
        "Можно пропустить. Тогда первая тренировка будет диагностической: жми Тяжело/Легко во время подходов, и следующие тренировки подстроятся."
    )


def _normalize(text: str) -> str:
    return text.lower().replace("ё", "е").strip()


def _numbers(line: str) -> tuple[float, int] | None:
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:кг|kg)?\s*[xх× ]\s*(\d{1,2})", line, re.IGNORECASE)
    if not match:
        nums = re.findall(r"\d+(?:[.,]\d+)?", line)
        if len(nums) < 2:
            return None
        weight_raw, reps_raw = nums[-2], nums[-1]
    else:
        weight_raw, reps_raw = match.group(1), match.group(2)
    weight = float(weight_raw.replace(",", "."))
    reps = int(float(reps_raw.replace(",", ".")))
    if not (1 <= reps <= 30 and 1 <= weight <= 500):
        return None
    return weight, reps


def _anchor_for_line(line: str) -> StrengthAnchor | None:
    normalized = _normalize(line)
    for anchor in ANCHORS:
        if any(_normalize(keyword) in normalized for keyword in anchor.keywords):
            return anchor
    return None


def parse_strength_calibration(text: str) -> list[dict]:
    entries: list[dict] = []
    seen: set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        anchor = _anchor_for_line(line)
        values = _numbers(line)
        if not anchor or not values or anchor.key in seen:
            continue
        weight, reps = values
        entries.append({
            "key": anchor.key,
            "label_ru": anchor.label_ru,
            "label_en": anchor.label_en,
            "weight_kg": weight,
            "reps": reps,
            "estimated_1rm": estimate_1rm(weight, reps),
        })
        seen.add(anchor.key)
    return entries


def _primary_codes_for_entry(entry: dict) -> tuple[str, ...]:
    anchor = next((item for item in ANCHORS if item.key == entry.get("key")), None)
    return anchor.codes if anchor else ()


async def save_strength_calibration(session: AsyncSession, user_id: int, text: str) -> list[dict]:
    entries = parse_strength_calibration(text)
    if not entries:
        return []

    session.add(CalibrationAnswer(
        user_id=user_id,
        question_key="strength_calibration",
        answer={"entries": entries, "source": "onboarding", "date": datetime.utcnow().isoformat()},
    ))

    for entry in entries:
        codes = _primary_codes_for_entry(entry)
        if not codes:
            continue
        exercises = (
            await session.execute(select(Exercise).where(Exercise.code.in_(list(codes))))
        ).scalars().all()
        for ex in exercises:
            for record_type, value in (
                ("estimated_1rm", entry["estimated_1rm"]),
                ("max_weight", entry["weight_kg"]),
            ):
                existing = (
                    await session.execute(
                        select(PersonalRecord).where(
                            PersonalRecord.user_id == user_id,
                            PersonalRecord.exercise_id == ex.id,
                            PersonalRecord.record_type == record_type,
                        )
                    )
                ).scalar_one_or_none()
                if existing:
                    existing.value = value
                    existing.achieved_at = datetime.utcnow()
                else:
                    session.add(PersonalRecord(
                        user_id=user_id,
                        exercise_id=ex.id,
                        record_type=record_type,
                        value=value,
                        achieved_at=datetime.utcnow(),
                    ))
    await session.flush()
    return entries


def working_weight_from_e1rm(e1rm: float, target_reps: int, exercise_type: ExerciseType) -> float:
    if e1rm <= 0:
        return 0.0
    reserve_factor = 0.88 if exercise_type == ExerciseType.compound else 0.82
    raw = (e1rm / (1 + target_reps / 30)) * reserve_factor
    step = 2.5 if exercise_type == ExerciseType.compound else 1.25
    return max(0.0, round(raw / step) * step)


async def calibrated_start_weight(
    session: AsyncSession,
    user_id: int,
    exercise: Exercise,
    target_reps: int,
) -> float | None:
    exact = (
        await session.execute(
            select(PersonalRecord.value)
            .where(
                PersonalRecord.user_id == user_id,
                PersonalRecord.exercise_id == exercise.id,
                PersonalRecord.record_type == "estimated_1rm",
            )
        )
    ).scalar_one_or_none()
    if exact:
        return working_weight_from_e1rm(float(exact), target_reps, exercise.exercise_type)

    answer = (
        await session.execute(
            select(CalibrationAnswer.answer)
            .where(
                CalibrationAnswer.user_id == user_id,
                CalibrationAnswer.question_key == "strength_calibration",
            )
            .order_by(CalibrationAnswer.answered_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if not answer:
        return None

    entries = answer.get("entries") if isinstance(answer, dict) else None
    if not entries:
        return None

    for anchor in ANCHORS:
        ratio = anchor.ratios.get(exercise.code)
        if not ratio:
            continue
        entry = next((item for item in entries if item.get("key") == anchor.key), None)
        if not entry:
            continue
        e1rm = float(entry.get("estimated_1rm") or 0) * ratio
        weight = working_weight_from_e1rm(e1rm, target_reps, exercise.exercise_type)
        return weight if weight > 0 else None
    return None
