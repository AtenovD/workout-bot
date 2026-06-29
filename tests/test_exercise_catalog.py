from scripts import seed_data


def _seed_exercises():
    curated_extra = [
        e for e in seed_data.ALL_EXTRA_EXERCISES
        if e["code"] in seed_data.CURATED_EXTRA_CODES
    ]
    return (
        seed_data.EXERCISES_CHEST_BACK
        + seed_data.EXERCISES_REST
        + seed_data.EXERCISES_NEW
        + curated_extra
        + seed_data.CURATED_GYM_EXERCISES
    )


def _normalized(ex):
    return {**ex, **seed_data.EXERCISE_OVERRIDES.get(ex["code"], {})}


def test_active_exercise_catalog_has_valid_references_and_media():
    equipment_codes = {item["code"] for item in seed_data.EQUIPMENT_DATA}
    muscle_codes = {item["code"] for item in seed_data.MUSCLE_GROUP_DATA}
    bad = []

    for raw in _seed_exercises():
        ex = _normalized(raw)
        if not ex.get("is_active", ex["code"] not in seed_data.INACTIVE_EXERCISE_CODES):
            continue

        muscle = ex.get("muscle")
        equipment = ex.get("equipment")
        resolved_equipment = seed_data.EQUIPMENT_ALIASES.get(equipment, equipment) if equipment else None
        has_media = bool(ex.get("gif_url") or ex.get("photo_url") or ex.get("video_url"))

        if muscle not in muscle_codes:
            bad.append(f"{ex['code']}: bad muscle {muscle}")
        if resolved_equipment and resolved_equipment not in equipment_codes:
            bad.append(f"{ex['code']}: bad equipment {equipment}->{resolved_equipment}")
        if not has_media:
            bad.append(f"{ex['code']}: missing media")

    assert bad == []


def test_equipment_catalog_has_clean_labels():
    names = [item["name_ru"] for item in seed_data.EQUIPMENT_DATA]
    codes = [item["code"] for item in seed_data.EQUIPMENT_DATA]

    assert len(names) == len(set(names))
    assert len(codes) == len(set(codes))
    assert "Тяга верхнего блока" not in names
    assert "Жим ногами" not in names
    assert "Тренажёр верхней тяги" in names
    assert "Тренажёр жим ногами" in names


def test_trx_and_hiit_are_not_seeded_as_active_bodyweight_gym_work():
    by_code = {ex["code"]: _normalized(ex) for ex in _seed_exercises()}

    assert by_code["trx_pushup"]["equipment"] == "trx"
    assert by_code["trx_row"]["equipment"] == "trx"
    assert "Other" not in seed_data.EQUIPMENT_ALIASES

    for code in ["burpee", "burpees", "jump_squat", "pistol_squat", "pike_pushup"]:
        assert code in seed_data.INACTIVE_EXERCISE_CODES
