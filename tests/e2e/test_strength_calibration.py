import pytest
from sqlalchemy import select

from models.exercise import Exercise
from models.personal_record import PersonalRecord
from services.strength_calibration import calibrated_start_weight, save_strength_calibration


@pytest.mark.asyncio
async def test_strength_calibration_saves_records_and_feeds_start_weight(session, registered_user):
    entries = await save_strength_calibration(
        session,
        registered_user.id,
        "Жим лежа 80x8\nПрисед 100x5",
    )
    await session.flush()

    bench = (
        await session.execute(select(Exercise).where(Exercise.code == "bench_press"))
    ).scalar_one()
    pr = (
        await session.execute(
            select(PersonalRecord).where(
                PersonalRecord.user_id == registered_user.id,
                PersonalRecord.exercise_id == bench.id,
                PersonalRecord.record_type == "estimated_1rm",
            )
        )
    ).scalar_one()
    start_weight = await calibrated_start_weight(session, registered_user.id, bench, target_reps=8)

    assert [entry["key"] for entry in entries] == ["bench_press", "squat"]
    assert float(pr.value) > 100
    assert start_weight == 70.0
