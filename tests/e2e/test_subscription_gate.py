from datetime import datetime

import pytest
from aiogram import types
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.services.admin_access import set_admins
from bot.services.subscription_gate import normalize_required_channel, set_required_en_channel
from models.app_setting import AppSetting
from models.profile import Profile
from models.user import User


def _msg(text: str, uid: int = 123456789) -> types.Message:
    return types.Message(
        message_id=1,
        date=datetime.utcnow(),
        chat=types.Chat(id=uid, type="private", username="u", first_name="T"),
        from_user=types.User(id=uid, is_bot=False, first_name="T", username="u", language_code="en"),
        text=text,
    )


def _cb(data: str, uid: int = 123456789) -> types.CallbackQuery:
    return types.CallbackQuery(
        id=f"cb_{data}",
        from_user=types.User(id=uid, is_bot=False, first_name="T", username="u", language_code="en"),
        chat_instance=str(uid),
        message=types.Message(
            message_id=10,
            date=datetime.utcnow(),
            chat=types.Chat(id=uid, type="private", username="u", first_name="T"),
        ),
        data=data,
    )


async def _feed_message(dispatcher, bot, session, text: str, uid: int = 123456789):
    bot.session.requests.clear()
    update = types.Update(
        update_id=abs(hash((text, datetime.utcnow().timestamp()))) % 10_000_000,
        message=_msg(text, uid),
    )
    await dispatcher.feed_update(bot=bot, update=update, session=session)
    return list(bot.session.requests)


async def _feed_callback(dispatcher, bot, session, data: str, uid: int = 123456789):
    bot.session.requests.clear()
    update = types.Update(
        update_id=abs(hash((data, datetime.utcnow().timestamp()))) % 10_000_000,
        callback_query=_cb(data, uid),
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


def _callbacks(requests):
    values = []
    for request in requests:
        markup = request["payload"].get("reply_markup")
        if not isinstance(markup, dict):
            continue
        for row in markup.get("inline_keyboard") or []:
            values.extend(button.get("callback_data") for button in row if button.get("callback_data"))
    return values


async def _set_channel(engine, channel="@gym_updates"):
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as setup:
        await setup.execute(delete(AppSetting))
        await set_required_en_channel(setup, channel)
        await setup.commit()


@pytest.mark.asyncio
async def test_existing_english_user_is_blocked_until_subscribed(dispatcher, bot, session, engine, registered_user):
    await _set_channel(engine)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as setup:
        user = (await setup.execute(select(User).where(User.telegram_id == registered_user.telegram_id))).scalar_one()
        user.language_code = "en"
        await setup.commit()

    bot.session.chat_member_status = "left"
    requests = await _feed_message(dispatcher, bot, session, "/start", registered_user.telegram_id)

    assert "Subscription required" in _texts(requests)
    assert "sub:check" in _callbacks(requests)
    assert "GYM Control Center" not in _texts(requests)


@pytest.mark.asyncio
async def test_subscribed_english_user_enters_main_menu(dispatcher, bot, session, engine, registered_user):
    await _set_channel(engine)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as setup:
        user = (await setup.execute(select(User).where(User.telegram_id == registered_user.telegram_id))).scalar_one()
        user.language_code = "en"
        await setup.commit()

    bot.session.chat_member_status = "member"
    requests = await _feed_message(dispatcher, bot, session, "/start", registered_user.telegram_id)

    assert "GYM Control Center" in _texts(requests)
    assert "Subscription required" not in _texts(requests)


@pytest.mark.asyncio
async def test_private_invite_with_chat_id_is_checked_by_numeric_chat_id(dispatcher, bot, session, engine, registered_user):
    await _set_channel(engine, "-1001234567890 https://t.me/+abc123")
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as setup:
        user = (await setup.execute(select(User).where(User.telegram_id == registered_user.telegram_id))).scalar_one()
        user.language_code = "en"
        await setup.commit()

    bot.session.chat_member_status = "member"
    requests = await _feed_message(dispatcher, bot, session, "/start", registered_user.telegram_id)
    get_member = [r for r in requests if r["method"] == "getChatMember"]

    assert get_member
    assert get_member[0]["payload"]["chat_id"] == "-1001234567890"
    assert "GYM Control Center" in _texts(requests)


@pytest.mark.asyncio
async def test_verification_error_keeps_english_user_locked(dispatcher, bot, session, engine, registered_user):
    await _set_channel(engine)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as setup:
        user = (await setup.execute(select(User).where(User.telegram_id == registered_user.telegram_id))).scalar_one()
        user.language_code = "en"
        await setup.commit()

    bot.session.chat_member_status = "error"
    requests = await _feed_message(dispatcher, bot, session, "/start", registered_user.telegram_id)

    assert "Subscription required" in _texts(requests)
    assert "sub:check" in _callbacks(requests)
    assert "GYM Control Center" not in _texts(requests)


@pytest.mark.asyncio
async def test_new_user_selecting_english_gets_subscription_gate(dispatcher, bot, session, engine):
    await _set_channel(engine)
    uid = 919191
    bot.session.chat_member_status = "left"

    requests = await _feed_callback(dispatcher, bot, session, "onboarding_lang:en", uid)

    assert "Subscription required" in _texts(requests)
    assert "sub:check" in _callbacks(requests)


@pytest.mark.asyncio
async def test_admin_can_set_required_english_channel(dispatcher, bot, session):
    admin_uid = 700700
    set_admins([admin_uid])

    await _feed_message(dispatcher, bot, session, "/admin", admin_uid)
    prompt = await _feed_callback(dispatcher, bot, session, "admin:channel", admin_uid)
    assert "EN required channel" in _texts(prompt)

    saved = await _feed_message(dispatcher, bot, session, "@new_gym_channel", admin_uid)
    assert "enabled" in _texts(saved)
    assert "@new_gym_channel" in _texts(saved)


@pytest.mark.asyncio
async def test_admin_rejects_private_invite_without_chat_id(dispatcher, bot, session):
    admin_uid = 700701
    set_admins([admin_uid])

    await _feed_message(dispatcher, bot, session, "/admin", admin_uid)
    await _feed_callback(dispatcher, bot, session, "admin:channel", admin_uid)
    saved = await _feed_message(dispatcher, bot, session, "https://t.me/+abc123", admin_uid)

    assert "cannot be verified" in _texts(saved)
    assert "-1001234567890" in _texts(saved)


def test_channel_normalization_supports_private_chat_id_plus_invite():
    private = normalize_required_channel("-1001234567890 https://t.me/+abc123")
    invite_only = normalize_required_channel("https://t.me/+abc123")

    assert private is not None
    assert private.chat_ref == "-1001234567890"
    assert private.url == "https://t.me/+abc123"
    assert private.verifiable is True
    assert invite_only is not None
    assert invite_only.verifiable is False
