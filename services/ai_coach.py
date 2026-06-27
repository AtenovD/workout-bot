"""Low-token Groq coach review for future workout adjustments."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.exercise import Exercise, MuscleGroup
from models.profile import Profile
from models.workout import ExerciseSet, SessionExercise, WorkoutReview, WorkoutSession


GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"

ALLOWED_INTENSITY = {"much_easier", "slightly_easier", "keep", "slightly_harder"}
MAX_LIST_ITEMS = 8


@dataclass(frozen=True)
class AICoachResult:
    adjustment: dict[str, Any] | None
    coach_note: str | None = None
    model: str | None = None
    error: str | None = None


def _clamp_float(value: Any, default: float, low: float, high: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, number))


def _clamp_int(value: Any, default: int, low: int, high: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, number))


def _clean_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned = []
    for item in value[:MAX_LIST_ITEMS]:
        if isinstance(item, str):
            item = item.strip()
            if item:
                cleaned.append(item[:64])
    return cleaned


def sanitize_ai_adjustment(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {}

    intensity = raw.get("intensity_delta")
    if intensity not in ALLOWED_INTENSITY:
        intensity = "keep"

    adjustment = {
        "intensity_delta": intensity,
        "sets_delta": _clamp_int(raw.get("sets_delta"), 0, -2, 1),
        "weight_factor": _clamp_float(raw.get("weight_factor"), 1.0, 0.75, 1.10),
        "rest_factor": _clamp_float(raw.get("rest_factor"), 1.0, 0.85, 1.35),
        "avoid_exercise_codes": _clean_str_list(raw.get("avoid_exercise_codes")),
        "prefer_exercise_codes": _clean_str_list(raw.get("prefer_exercise_codes")),
        "reduce_muscle_groups": _clean_str_list(raw.get("reduce_muscle_groups")),
        "focus_muscle_groups": _clean_str_list(raw.get("focus_muscle_groups")),
    }

    note = raw.get("coach_note")
    if isinstance(note, str):
        adjustment["coach_note"] = note.strip()[:400]
    return adjustment


async def _workout_context(
    session: AsyncSession,
    user_id: int,
    workout_session_id: int,
    review: WorkoutReview,
) -> dict[str, Any]:
    ws = await session.get(WorkoutSession, workout_session_id)
    profile = (await session.execute(select(Profile).where(Profile.user_id == user_id))).scalar_one_or_none()

    muscle_rows = await session.execute(select(MuscleGroup.id, MuscleGroup.code, MuscleGroup.name_ru))
    muscles = {row.id: {"code": row.code, "name": row.name_ru} for row in muscle_rows.all()}

    rows = await session.execute(
        select(SessionExercise, Exercise)
        .join(Exercise, SessionExercise.exercise_id == Exercise.id)
        .where(SessionExercise.session_id == workout_session_id)
        .order_by(SessionExercise.order_index)
    )

    exercises = []
    for se, ex in rows.all():
        sets_res = await session.execute(
            select(ExerciseSet).where(ExerciseSet.session_exercise_id == se.id).order_by(ExerciseSet.set_number)
        )
        sets = sets_res.scalars().all()
        work_sets = [s for s in sets if not s.is_warmup]
        rpes = [s.rpe for s in work_sets if s.rpe is not None]
        muscle = muscles.get(ex.primary_muscle_group_id or 0, {})
        exercises.append({
            "code": ex.code,
            "name": ex.name_ru,
            "muscle": muscle.get("code"),
            "planned": {
                "sets": se.target_sets,
                "reps": se.target_reps,
                "weight_kg": float(se.target_weight_kg or 0),
                "rest_seconds": se.rest_seconds,
            },
            "completed_sets": len(work_sets),
            "was_skipped": bool(se.was_skipped),
            "rpe_signals": rpes[:6],
        })

    return {
        "workout": {
            "id": workout_session_id,
            "difficulty_modifier": ws.difficulty_modifier.value if ws and ws.difficulty_modifier else None,
            "duration_min": ws.duration_min if ws else None,
            "total_volume_kg": float(ws.total_volume_kg or 0) if ws else 0,
        },
        "profile": {
            "goal": profile.goal.value if profile and profile.goal else None,
            "experience": profile.experience_level.value if profile and profile.experience_level else None,
            "training_structure": profile.training_structure.value if profile and profile.training_structure else None,
            "split_type": profile.split_type.value if profile and profile.split_type else None,
            "preferred_duration_min": profile.preferred_duration_min if profile else None,
            "health_flags": profile.health_flags if profile else [],
        },
        "review": {
            "intensity_feedback": review.intensity_feedback,
            "pain_feedback": review.pain_feedback,
            "skipped_exercise_codes": [item["code"] for item in exercises if item["was_skipped"]],
            "skipped_exercise_names": review.skipped_exercise_names or [],
        },
        "exercises": exercises,
    }


def _system_prompt() -> str:
    return (
        "You are a conservative strength-training planning analyst. "
        "Return only valid JSON. Do not diagnose injuries. "
        "Never increase load when pain_feedback is pain. "
        "Use exercise codes and muscle group codes from the input only when possible."
    )


def _user_prompt(context: dict[str, Any]) -> str:
    return (
        "Analyze this completed workout and return a small JSON object for the next workout generator.\n"
        "Schema:\n"
        "{"
        "\"intensity_delta\":\"much_easier|slightly_easier|keep|slightly_harder\","
        "\"sets_delta\":-2..1,"
        "\"weight_factor\":0.75..1.10,"
        "\"rest_factor\":0.85..1.35,"
        "\"avoid_exercise_codes\":[string],"
        "\"prefer_exercise_codes\":[string],"
        "\"reduce_muscle_groups\":[string],"
        "\"focus_muscle_groups\":[string],"
        "\"coach_note\":\"short Russian note, max 1 sentence\""
        "}.\n"
        f"Workout JSON:\n{json.dumps(context, ensure_ascii=False, separators=(',', ':'))}"
    )


async def analyze_workout_review(
    session: AsyncSession,
    user_id: int,
    workout_session_id: int,
    review: WorkoutReview,
) -> AICoachResult:
    if not settings.GROQ_API_KEY:
        return AICoachResult(adjustment=None, error="groq_api_key_missing")

    context = await _workout_context(session, user_id, workout_session_id, review)
    payload = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": _system_prompt()},
            {"role": "user", "content": _user_prompt(context)},
        ],
        "temperature": 0.2,
        "max_tokens": 450,
        "response_format": {"type": "json_object"},
    }

    try:
        async with httpx.AsyncClient(timeout=settings.GROQ_TIMEOUT_SECONDS) as client:
            response = await client.post(
                GROQ_CHAT_COMPLETIONS_URL,
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            raw_adjustment = json.loads(content)
    except Exception as exc:
        return AICoachResult(adjustment=None, model=settings.GROQ_MODEL, error=type(exc).__name__[:128])

    adjustment = sanitize_ai_adjustment(raw_adjustment)
    return AICoachResult(
        adjustment=adjustment,
        coach_note=adjustment.get("coach_note"),
        model=settings.GROQ_MODEL,
        error=None,
    )
