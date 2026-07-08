from __future__ import annotations

from dataclasses import dataclass
from html import escape

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.app_setting import AppSetting
from models.user import User

REQUIRED_EN_CHANNEL_KEY = "required_en_channel"
ALLOWED_MEMBER_STATUSES = {"creator", "administrator", "member"}


@dataclass(frozen=True)
class ChannelRef:
    raw: str
    chat_ref: str
    url: str
    display: str


@dataclass(frozen=True)
class SubscriptionCheck:
    ok: bool
    verify_error: bool = False


def normalize_required_channel(raw: str | None) -> ChannelRef | None:
    value = (raw or "").strip()
    if not value:
        return None
    if value.lower() in {"off", "clear", "none", "-", "disable", "disabled"}:
        return None

    if value.startswith("https://t.me/") or value.startswith("http://t.me/"):
        url = value.replace("http://", "https://", 1)
        slug = url.split("t.me/", 1)[1].strip("/")
        if slug and not slug.startswith("+"):
            chat_ref = f"@{slug.split('/', 1)[0]}"
        else:
            chat_ref = value
        return ChannelRef(raw=value, chat_ref=chat_ref, url=url, display=url)

    if value.startswith("t.me/"):
        return normalize_required_channel(f"https://{value}")

    if value.startswith("@"):
        slug = value[1:].strip()
        if not slug:
            return None
        return ChannelRef(raw=f"@{slug}", chat_ref=f"@{slug}", url=f"https://t.me/{slug}", display=f"@{slug}")

    if value.replace("_", "").isalnum():
        return ChannelRef(raw=f"@{value}", chat_ref=f"@{value}", url=f"https://t.me/{value}", display=f"@{value}")

    return None


async def get_required_en_channel(session: AsyncSession) -> ChannelRef | None:
    row = await session.get(AppSetting, REQUIRED_EN_CHANNEL_KEY)
    return normalize_required_channel(row.value if row else None)


async def set_required_en_channel(session: AsyncSession, raw: str | None) -> ChannelRef | None:
    channel = normalize_required_channel(raw)
    row = await session.get(AppSetting, REQUIRED_EN_CHANNEL_KEY)
    if not channel:
        if row:
            await session.delete(row)
        await session.flush()
        return None

    if row:
        row.value = channel.raw
    else:
        session.add(AppSetting(key=REQUIRED_EN_CHANNEL_KEY, value=channel.raw))
    await session.flush()
    return channel


async def check_required_subscription(bot: Bot, session: AsyncSession, user: User) -> SubscriptionCheck:
    if (user.language_code or "ru") != "en":
        return SubscriptionCheck(ok=True)

    channel = await get_required_en_channel(session)
    if not channel:
        return SubscriptionCheck(ok=True)

    try:
        member = await bot.get_chat_member(channel.chat_ref, user.telegram_id)
    except Exception:
        return SubscriptionCheck(ok=False, verify_error=True)

    status = member.get("status") if isinstance(member, dict) else getattr(member, "status", None)
    status_value = getattr(status, "value", status)
    return SubscriptionCheck(ok=status_value in ALLOWED_MEMBER_STATUSES)


async def has_required_subscription(bot: Bot, session: AsyncSession, user: User) -> bool:
    return (await check_required_subscription(bot, session, user)).ok


async def should_block_for_subscription(bot: Bot, session: AsyncSession, user: User) -> bool:
    if (user.language_code or "ru") != "en":
        return False
    channel = await get_required_en_channel(session)
    if not channel:
        return False
    return not await has_required_subscription(bot, session, user)


def subscription_gate_markup(channel: ChannelRef) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Subscribe", url=channel.url)],
            [InlineKeyboardButton(text="✅ Check subscription", callback_data="sub:check")],
        ]
    )


def subscription_gate_text(channel: ChannelRef) -> str:
    return (
        "🔒 <b>Subscription required</b>\n\n"
        "Before using the English version of the bot, please subscribe to our Telegram channel.\n\n"
        f"Channel: <b>{escape(channel.display)}</b>\n\n"
        "Tap <b>Subscribe</b>, then return here and press <b>Check subscription</b>."
    )


def subscription_verify_error_text(channel: ChannelRef) -> str:
    return (
        "🔒 <b>Subscription required</b>\n\n"
        "I could not verify your subscription right now, so access stays locked.\n\n"
        f"Channel: <b>{escape(channel.display)}</b>\n\n"
        "Please subscribe and press <b>Check subscription</b> again. If this keeps happening, the channel setup needs admin attention."
    )


async def send_subscription_gate(message: Message, session: AsyncSession) -> None:
    channel = await get_required_en_channel(session)
    if not channel:
        return
    await message.answer(subscription_gate_text(channel), reply_markup=subscription_gate_markup(channel), parse_mode="HTML")
