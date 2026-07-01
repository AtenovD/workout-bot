import pytest
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from sqlalchemy import select

from bot.states.states import OnboardingStates
from models.calibration import CalibrationAnswer
from models.exercise import Exercise
from models.exercise import EquipmentCategory, ExerciseType
from models.personal_record import PersonalRecord
from services.strength_calibration import calibrated_start_weight, save_strength_calibration


def _msg(text: str, uid: int) -> types.Message:
    from datetime import datetime

    return types.Message(
        message_id=1,
        date=datetime.utcnow(),
        chat=types.Chat(id=uid, type="private", username="u", first_name="T"),
        from_user=types.User(id=uid, is_bot=False, first_name="T", username="u"),
        text=text,
    )


async def _feed_message(dispatcher, bot, session, text: str, uid: int):
    bot.session.requests.clear()
    update = types.Update(update_id=abs(hash((text, uid))) % 10_000_000, message=_msg(text, uid))
    await dispatcher.feed_update(bot=bot, update=update, session=session)
    return list(bot.session.requests)


def _texts(requests):
    return "\n".join(
        request["payload"].get(key, "")
        for request in requests
        for key in ("text", "caption")
        if request["payload"].get(key)
    )


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


@pytest.mark.asyncio
async def test_strength_calibration_message_flow_accepts_english_working_weights(
    dispatcher,
    bot,
    session,
    registered_user,
):
    registered_user.language_code = "en"
    uid = registered_user.telegram_id
    key = StorageKey(bot_id=bot.id, chat_id=uid, user_id=uid)
    ctx = FSMContext(storage=dispatcher.storage, key=key)
    await ctx.set_state(OnboardingStates.strength_calibration_input)
    await ctx.set_data({
        "language": "en",
        "gender": "male",
        "age": 30,
        "height_cm": 180,
        "current_weight_kg": 90,
        "target_weight_kg": 95,
        "goal": "mass_gain",
        "experience_level": "intermediate",
        "experience_months": 24,
        "health_flags": [],
        "equipment_ids": [],
        "days_per_week": 4,
        "preferred_duration_min": 60,
    })

    requests = await _feed_message(dispatcher, bot, session, "bench press 100x10\nback row 90x9", uid)
    text = _texts(requests)
    saved = (
        await session.execute(
            select(CalibrationAnswer).where(
                CalibrationAnswer.user_id == registered_user.id,
                CalibrationAnswer.question_key == "strength_calibration",
            )
        )
    ).scalar_one_or_none()

    assert "Calibration complete" in text
    assert "Bench press 100x10" in text
    assert saved is not None
    assert [entry["key"] for entry in saved.answer["entries"]] == ["bench_press", "row"]
