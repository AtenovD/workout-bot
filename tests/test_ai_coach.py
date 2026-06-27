from services.ai_coach import sanitize_ai_adjustment


def test_sanitize_ai_adjustment_clamps_numbers_and_lists():
    raw = {
        "intensity_delta": "reckless",
        "sets_delta": 10,
        "weight_factor": 2.0,
        "rest_factor": 0.1,
        "avoid_exercise_codes": ["overhead_press", "", 123, "deadlift"],
        "prefer_exercise_codes": ["machine_press"],
        "reduce_muscle_groups": ["front_delts"],
        "focus_muscle_groups": ["chest"],
        "coach_note": "x" * 500,
    }

    adjustment = sanitize_ai_adjustment(raw)

    assert adjustment["intensity_delta"] == "keep"
    assert adjustment["sets_delta"] == 1
    assert adjustment["weight_factor"] == 1.1
    assert adjustment["rest_factor"] == 0.85
    assert adjustment["avoid_exercise_codes"] == ["overhead_press", "deadlift"]
    assert adjustment["prefer_exercise_codes"] == ["machine_press"]
    assert adjustment["reduce_muscle_groups"] == ["front_delts"]
    assert adjustment["focus_muscle_groups"] == ["chest"]
    assert len(adjustment["coach_note"]) == 400


def test_sanitize_ai_adjustment_accepts_empty_response():
    adjustment = sanitize_ai_adjustment(None)

    assert adjustment["intensity_delta"] == "keep"
    assert adjustment["sets_delta"] == 0
    assert adjustment["weight_factor"] == 1.0
    assert adjustment["rest_factor"] == 1.0
