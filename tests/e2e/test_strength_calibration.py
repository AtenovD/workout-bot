import pytest
from sqlalchemy import select

from models.exercise import Exercise
from models.exercise import EquipmentCategory, ExerciseType
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


@pytest.mark.asyncio
async def test_strength_anchors_transfer_to_related_exercises(session, registered_user):
    await save_strength_calibration(
        session,
        registered_user.id,
        "Жим лежа 80x8\nПрисед 100x5",
    )

    db_press = (
        await session.execute(select(Exercise).where(Exercise.code == "db_bench_press"))
    ).scalar_one_or_none()
    if db_press is None:
        db_press = Exercise(
            id=1001,
            code="db_bench_press",
            name_ru="Жим гантелей лежа",
            name_en="Dumbbell Bench Press",
            primary_muscle_group_id=2,
            equipment_category=EquipmentCategory.portable,
            exercise_type=ExerciseType.compound,
            difficulty=2,
            is_active=True,
        )
        session.add(db_press)
        await session.flush()

    leg_press = Exercise(
        id=1002,
        code="leg_press",
        name_ru="Жим ногами",
        name_en="Leg Press",
        primary_muscle_group_id=1,
        equipment_category=EquipmentCategory.stationary,
        exercise_type=ExerciseType.compound,
        difficulty=3,
        is_active=True,
    )
    session.add(leg_press)
    await session.flush()

    db_weight = await calibrated_start_weight(session, registered_user.id, db_press, target_reps=8)
    leg_press_weight = await calibrated_start_weight(session, registered_user.id, leg_press, target_reps=10)

    assert db_weight and db_weight > 20
    assert leg_press_weight and leg_press_weight > 120
