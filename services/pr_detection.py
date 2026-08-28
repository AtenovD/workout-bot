"""
Personal Record detection service.

Called after workout finish. Scans all logged sets, computes:
  - max_weight  : heaviest single set weight
  - max_reps    : most reps in a single set
  - max_volume  : total volume (reps * weight) in a single set
  - estimated_1rm: Epley formula 1RM

Compares with existing PRs; upserts where a new record was set.
Returns list of beaten PR descriptions for the summary message.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal

from models.workout import WorkoutSession, SessionExercise, ExerciseSet
from models.personal_record import PersonalRecord
from models.exercise import Exercise


def _epley_1rm(weight: float, reps: int) -> float:
    if reps == 1:
        return weight
    return weight * (1 + reps / 30)


async def detect_prs(session: AsyncSession, user_id: int, workout_id: int) -> list[str]:
    """Returns human-readable list of new PR messages."""
    # Load all sets for this workout
    result = await session.execute(
        select(ExerciseSet, SessionExercise, Exercise)
        .join(SessionExercise, ExerciseSet.session_exercise_id == SessionExercise.id)
        .join(Exercise, SessionExercise.exercise_id == Exercise.id)
        .join(WorkoutSession, SessionExercise.session_id == WorkoutSession.id)
        .where(WorkoutSession.id == workout_id)
    )
    rows = result.all()

    # Aggregate per exercise
    stats: dict[int, dict] = {}
    exercise_names: dict[int, str] = {}
    for es, se, ex in rows:
        eid = ex.id
        exercise_names[eid] = getattr(ex, 'name_ru', ex.name)
        s = stats.setdefault(eid, {
            'max_weight': 0.0, 'max_reps': 0,
            'max_volume': 0.0, 'est_1rm': 0.0,
        })
        w = float(es.weight_kg or 0)
        r = int(es.reps_done or 0)
        vol = w * r
        s['max_weight'] = max(s['max_weight'], w)
        s['max_reps'] = max(s['max_reps'], r)
        s['max_volume'] = max(s['max_volume'], vol)
        s['est_1rm'] = max(s['est_1rm'], _epley_1rm(w, r))

    if not stats:
        return []

    new_prs = []
    for eid, vals in stats.items():
        for rtype, value in [
            ('max_weight', vals['max_weight']),
            ('max_reps', vals['max_reps']),
            ('max_volume', vals['max_volume']),
            ('estimated_1rm', vals['est_1rm']),
        ]:
            if value <= 0:
                continue
            # Load existing PR
            res = await session.execute(
                select(PersonalRecord).where(
                    PersonalRecord.user_id == user_id,
                    PersonalRecord.exercise_id == eid,
                    PersonalRecord.record_type == rtype,
                )
            )
            existing: PersonalRecord | None = res.scalar_one_or_none()

            if existing is None or float(existing.value) < value:
                if existing is None:
                    existing = PersonalRecord(
                        user_id=user_id, exercise_id=eid, record_type=rtype
                    )
                    session.add(existing)
                existing.value = Decimal(str(round(value, 2)))
                from datetime import datetime
                existing.achieved_at = datetime.utcnow()

                name = exercise_names[eid]
                if rtype == 'max_weight':
                    new_prs.append(f"🏆 <b>PR!</b> {name} — вес {value:.1f} кг")
                elif rtype == 'max_reps':
                    new_prs.append(f"🏆 <b>PR!</b> {name} — {int(value)} повт.")
                elif rtype == 'max_volume':
                    new_prs.append(f"🏆 <b>PR!</b> {name} — объём {value:.0f} кг")
                elif rtype == 'estimated_1rm':
                    new_prs.append(f"🏆 <b>PR!</b> {name} — расч. 1ПМ {value:.1f} кг")

    if new_prs:
        await session.commit()
    return new_prs
