from datetime import datetime

import pytest
from aiogram import types

from bot.services.admin_access import set_admins


def _cb(data: str, uid: int = 123456789) -> types.CallbackQuery:
    return types.CallbackQuery(
        id=f"cb_{data}",
        from_user=types.User(id=uid, is_bot=False, first_name="T", username="u"),
        chat_instance=str(uid),
        message=types.Message(
            message_id=10,
            date=datetime.utcnow(),
            chat=types.Chat(id=uid, type="private", username="u", first_name="T"),
        ),
        data=data,
    )


async def _feed_callback(dispatcher, bot, session, data: str, uid: int = 123456789):
    bot.session.requests.clear()
    update = types.Update(
        update_id=abs(hash((data, datetime.utcnow().timestamp()))) % 10_000_000,
        callback_query=_cb(data, uid),
    )
    await dispatcher.feed_update(bot=bot, update=update, session=session)
    return list(bot.session.requests)


def _msg(text: str, uid: int = 123456789) -> types.Message:
    return types.Message(
        message_id=1,
        date=datetime.utcnow(),
        chat=types.Chat(id=uid, type="private", username="u", first_name="T"),
        from_user=types.User(id=uid, is_bot=False, first_name="T", username="u"),
        text=text,
    )


async def _feed_message(dispatcher, bot, session, text: str, uid: int = 123456789):
    bot.session.requests.clear()
    update = types.Update(
        update_id=abs(hash((text, datetime.utcnow().timestamp()))) % 10_000_000,
        message=_msg(text, uid),
    )
    await dispatcher.feed_update(bot=bot, update=update, session=session)
    return list(bot.session.requests)


def _texts(requests):
    values = []
    for request in requests:
        payload = request["payload"]
        for key in ("text", "caption"):
            if payload.get(key):
                values.append(payload[key])
    return "\n".join(values)


def _methods(requests):
    return [request["method"] for request in requests]


def _reply_callbacks(requests):
    callbacks = []
    for request in requests:
        markup = request["payload"].get("reply_markup")
        if not isinstance(markup, dict):
            continue
        for row in markup.get("inline_keyboard") or []:
            for button in row:
                if button.get("callback_data"):
                    callbacks.append(button["callback_data"])
    return callbacks


@pytest.mark.asyncio
async def test_main_menu_buttons_return_their_expected_sections(dispatcher, bot, session, registered_user):
    cases = {
        "menu:workout": ["Начинаем тренировку", "mod:light", "mod:normal", "mod:hard"],
        "menu:progress": ["Твой прогресс", "prog:vol_chart", "prog:weight_chart", "prog:records"],
        "gam:achieve": ["Достижения"],
        "menu:calibration": ["Калибровка", "cal:a:"],
        "menu:schedule": ["Расписание тренировок", "schedule:mode:fixed", "schedule:mode:spontaneous"],
        "menu:challenge": ["30-дневный челлендж", "challenge:join"],
        "menu:equipment": ["Выбери категорию инвентаря", "eq_cat:none", "eq_cat:portable", "eq_cat:stationary"],
        "menu:settings": ["Настройки", "settings:export", "settings:reset_confirm", "settings:language"],
    }

    for callback_data, expected in cases.items():
        requests = await _feed_callback(dispatcher, bot, session, callback_data, registered_user.telegram_id)
        rendered = _texts(requests) + "\n" + "\n".join(_reply_callbacks(requests))
        for token in expected:
            assert token in rendered, f"{callback_data} rendered wrong output: {rendered}"


@pytest.mark.asyncio
async def test_progress_subbuttons_return_expected_outputs(dispatcher, bot, session, registered_user):
    await _feed_callback(dispatcher, bot, session, "menu:progress", registered_user.telegram_id)

    volume = await _feed_callback(dispatcher, bot, session, "prog:vol_chart", registered_user.telegram_id)
    assert "sendPhoto" in _methods(volume)
    assert "Объём тренировок за 30 дней" in _texts(volume)

    weight = await _feed_callback(dispatcher, bot, session, "prog:weight_chart", registered_user.telegram_id)
    assert "sendPhoto" in _methods(weight)
    assert "Динамика веса за 90 дней" in _texts(weight)

    records = await _feed_callback(dispatcher, bot, session, "prog:records", registered_user.telegram_id)
    assert "Рекордов пока нет" in _texts(records)


@pytest.mark.asyncio
async def test_schedule_buttons_update_schedule_screen(dispatcher, bot, session, registered_user):
    fixed = await _feed_callback(dispatcher, bot, session, "schedule:mode:fixed", registered_user.telegram_id)
    assert "По дням недели" in _texts(fixed)
    assert "schedule:day:0" in _reply_callbacks(fixed)

    monday = await _feed_callback(dispatcher, bot, session, "schedule:day:0", registered_user.telegram_id)
    assert "Дни: <b>Пн</b>" in _texts(monday)

    reminder = await _feed_callback(dispatcher, bot, session, "schedule:toggle_reminder", registered_user.telegram_id)
    assert "Напоминание: ✅ включено" in _texts(reminder)

    set_time = await _feed_callback(dispatcher, bot, session, "schedule:set_time", registered_user.telegram_id)
    assert "Введи время напоминания" in _texts(set_time)


@pytest.mark.asyncio
async def test_settings_buttons_return_expected_outputs(dispatcher, bot, session, registered_user):
    lang_menu = await _feed_callback(dispatcher, bot, session, "settings:language", registered_user.telegram_id)
    assert "Выберите язык" in _texts(lang_menu)
    assert {"lang:ru", "lang:en"}.issubset(set(_reply_callbacks(lang_menu)))

    en = await _feed_callback(dispatcher, bot, session, "lang:en", registered_user.telegram_id)
    assert "English" in _texts(en)
    assert "menu:workout" in _reply_callbacks(en)

    confirm = await _feed_callback(dispatcher, bot, session, "settings:reset_confirm", registered_user.telegram_id)
    assert "Подтверждение сброса" in _texts(confirm)
    assert "settings:reset_do" in _reply_callbacks(confirm)

    export = await _feed_callback(dispatcher, bot, session, "settings:export", registered_user.telegram_id)
    assert "sendDocument" in _methods(export)
    assert "Ваши данные" in _texts(export)


@pytest.mark.asyncio
async def test_english_onboarding_keeps_english_after_language_choice(dispatcher, bot, session):
    uid = 777331

    language = await _feed_callback(dispatcher, bot, session, "onboarding_lang:en", uid)
    assert "Let's run a quick calibration" in _texts(language)
    assert "cal:start" in _reply_callbacks(language)

    gender = await _feed_callback(dispatcher, bot, session, "cal:start", uid)
    rendered = _texts(gender)
    assert "Step 1 / 11" in rendered
    assert "Gender" in rendered
    assert "Шаг 1 / 11" not in rendered


@pytest.mark.asyncio
async def test_equipment_buttons_follow_category_toggle_done_flow(dispatcher, bot, session, registered_user):
    category = await _feed_callback(dispatcher, bot, session, "eq_cat:stationary", registered_user.telegram_id)
    assert "Стационарный инвентарь" in _texts(category)
    toggle_buttons = [cb for cb in _reply_callbacks(category) if cb.startswith("eq_toggle:")]
    assert toggle_buttons

    toggled = await _feed_callback(dispatcher, bot, session, toggle_buttons[0], registered_user.telegram_id)
    assert "editMessageReplyMarkup" in _methods(toggled)

    done = await _feed_callback(dispatcher, bot, session, "eq_done", registered_user.telegram_id)
    assert "Готово" in _texts(done)
    assert "инвентаре" in _texts(done)


@pytest.mark.asyncio
async def test_workout_buttons_generate_and_control_session(dispatcher, bot, session, registered_user):
    overview = await _feed_callback(dispatcher, bot, session, "mod:hard", registered_user.telegram_id)
    assert "Стратегия:" in _texts(overview)
    begin_callbacks = [cb for cb in _reply_callbacks(overview) if cb.startswith("wk:begin:")]
    regen_callbacks = [cb for cb in _reply_callbacks(overview) if cb.startswith("wk:regen:")]
    assert begin_callbacks and regen_callbacks

    first_exercise = await _feed_callback(dispatcher, bot, session, begin_callbacks[0], registered_user.telegram_id)
    assert {"sendAnimation", "sendPhoto", "editMessageText"}.intersection(_methods(first_exercise))
    assert "Рабочий подход" in _texts(first_exercise) or "Разминочный подход" in _texts(first_exercise)
    exercise_callbacks = _reply_callbacks(first_exercise)
    assert any(cb.startswith("set:done:") for cb in exercise_callbacks)
    assert any(cb.startswith("set:hard:") for cb in exercise_callbacks)
    assert any(cb.startswith("set:easy:") for cb in exercise_callbacks)
    assert any(cb.startswith("set:replace:") for cb in exercise_callbacks)
    assert any(cb.startswith("set:skip:") for cb in exercise_callbacks)

    display = await _feed_callback(
        dispatcher,
        bot,
        session,
        next(cb for cb in exercise_callbacks if cb.startswith("set:rs:")),
        registered_user.telegram_id,
    )
    assert display[-1]["method"] == "answerCallbackQuery"

    hard = await _feed_callback(
        dispatcher,
        bot,
        session,
        next(cb for cb in exercise_callbacks if cb.startswith("set:hard:")),
        registered_user.telegram_id,
    )
    assert "editMessageReplyMarkup" in _methods(hard)

    regen = await _feed_callback(dispatcher, bot, session, regen_callbacks[0], registered_user.telegram_id)
    assert "Выбери интенсивность" in _texts(regen)


@pytest.mark.asyncio
async def test_stats_profile_measurement_reminder_referral_buttons(dispatcher, bot, session, registered_user):
    stats = await _feed_callback(dispatcher, bot, session, "menu:stats", registered_user.telegram_id)
    assert "Уровень" in _texts(stats)
    assert {"gam:achieve", "gam:records", "gam:history"}.issubset(set(_reply_callbacks(stats)))

    gam_records = await _feed_callback(dispatcher, bot, session, "gam:records", registered_user.telegram_id)
    assert "Рекорды" in _texts(gam_records)

    gam_history = await _feed_callback(dispatcher, bot, session, "gam:history", registered_user.telegram_id)
    assert "История тренировок" in _texts(gam_history)

    profile = await _feed_callback(dispatcher, bot, session, "menu:profile", registered_user.telegram_id)
    assert "Профиль" in _texts(profile)
    assert {"prof:update_weight", "prof:change_goal", "prof:recalibrate"}.issubset(set(_reply_callbacks(profile)))

    weight = await _feed_callback(dispatcher, bot, session, "prof:update_weight", registered_user.telegram_id)
    assert "Введи свой текущий вес" in _texts(weight)

    goals = await _feed_callback(dispatcher, bot, session, "prof:change_goal", registered_user.telegram_id)
    assert "Выбери новую цель" in _texts(goals)
    assert {"goal:mass_gain", "goal:weight_loss", "goal:maintenance", "goal:cardio"}.issubset(set(_reply_callbacks(goals)))

    measurements = await _feed_callback(dispatcher, bot, session, "menu:measurements", registered_user.telegram_id)
    assert "Замеры тела" in _texts(measurements)
    assert "meas:new" in _reply_callbacks(measurements)

    meas_new = await _feed_callback(dispatcher, bot, session, "meas:new", registered_user.telegram_id)
    assert "Новый замер" in _texts(meas_new)

    reminders = await _feed_callback(dispatcher, bot, session, "menu:reminders", registered_user.telegram_id)
    assert "Напоминания" in _texts(reminders)
    reminder_buttons = [cb for cb in _reply_callbacks(reminders) if cb.startswith("remind:toggle:")]
    assert reminder_buttons

    reminder_toggle = await _feed_callback(dispatcher, bot, session, reminder_buttons[0], registered_user.telegram_id)
    assert "Напоминания" in _texts(reminder_toggle)

    referral = await _feed_callback(dispatcher, bot, session, "menu:referral", registered_user.telegram_id)
    assert "Реферальная программа" in _texts(referral)
    assert "test_workout_bot" in _texts(referral)


@pytest.mark.asyncio
async def test_review_and_reset_buttons_return_expected_outputs(dispatcher, bot, session, registered_user):
    overview = await _feed_callback(dispatcher, bot, session, "mod:normal", registered_user.telegram_id)
    begin = next(cb for cb in _reply_callbacks(overview) if cb.startswith("wk:begin:"))
    started = await _feed_callback(dispatcher, bot, session, begin, registered_user.telegram_id)
    skip = next(cb for cb in _reply_callbacks(started) if cb.startswith("set:skip:"))
    skipped = await _feed_callback(dispatcher, bot, session, skip, registered_user.telegram_id)
    assert "editMessageReplyMarkup" in _methods(skipped)

    review = await _feed_callback(dispatcher, bot, session, "review:intensity:1:ok", registered_user.telegram_id)
    assert "самочувствию" in _texts(review)

    confirm = await _feed_callback(dispatcher, bot, session, "settings:reset_confirm", registered_user.telegram_id)
    assert "settings:reset_do" in _reply_callbacks(confirm)

    reset = await _feed_callback(dispatcher, bot, session, "settings:reset_do", registered_user.telegram_id)
    assert "Прогресс сброшен" in _texts(reset)


@pytest.mark.asyncio
async def test_admin_button_stats_and_segmented_broadcast(dispatcher, bot, session, registered_user):
    admin_uid = 555777
    set_admins([admin_uid])

    non_admin_menu = await _feed_callback(dispatcher, bot, session, "menu:main", registered_user.telegram_id)
    assert "menu:admin" not in _reply_callbacks(non_admin_menu)

    admin_menu = await _feed_callback(dispatcher, bot, session, "menu:main", admin_uid)
    main_menu_callbacks = []
    first_markup = admin_menu[0]["payload"].get("reply_markup")
    for row in first_markup.get("inline_keyboard") or []:
        main_menu_callbacks.extend(button.get("callback_data") for button in row)
    assert "menu:admin" not in main_menu_callbacks
    assert "menu:admin" in _reply_callbacks(admin_menu)

    panel = await _feed_callback(dispatcher, bot, session, "menu:admin", admin_uid)
    rendered = _texts(panel) + "\n" + "\n".join(_reply_callbacks(panel))
    assert "Админ-панель" in rendered
    assert "Пользователи" in rendered
    assert "Тренировки" in rendered
    assert "admin:broadcast:ru" in rendered
    assert "admin:broadcast:en" in rendered

    ask_ru = await _feed_callback(dispatcher, bot, session, "admin:broadcast:ru", admin_uid)
    assert "Рассылка RU" in _texts(ask_ru)

    sent_ru = await _feed_message(dispatcher, bot, session, "<b>RU news</b>", admin_uid)
    send_messages = [r for r in sent_ru if r["method"] == "sendMessage"]
    assert any(r["payload"].get("chat_id") == registered_user.telegram_id for r in send_messages)
    assert "Рассылка RU завершена" in _texts(sent_ru)

    ask_en = await _feed_callback(dispatcher, bot, session, "admin:broadcast:en", admin_uid)
    assert "Рассылка EN" in _texts(ask_en)

    sent_en = await _feed_message(dispatcher, bot, session, "EN news", admin_uid)
    assert "Рассылка EN завершена" in _texts(sent_en)
