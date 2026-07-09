from types import SimpleNamespace

from bot.handlers.workout import exercise_has_technique, exercise_log_kb, exercise_technique_url


def test_broken_raw_github_media_is_not_used_as_technique_url():
    ex = SimpleNamespace(
        code="bench_press",
        name_ru="Жим лёжа",
        name_en="Bench Press",
        gif_url="https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/0150/0150.gif",
        photo_url=None,
        video_url=None,
        instructions=["Lower the bar under control", "Press up"],
        tips=[],
        common_mistakes=[],
        description=None,
    )

    assert exercise_technique_url(ex) is None
    assert exercise_has_technique(ex) is True

    markup = exercise_log_kb(ex, 77, 1, 10, 60.0, lang="en")
    technique_buttons = [
        button
        for row in markup.inline_keyboard
        for button in row
        if "Technique" in button.text
    ]

    assert len(technique_buttons) == 1
    assert technique_buttons[0].url is None
    assert technique_buttons[0].callback_data == "set:tech:77"
