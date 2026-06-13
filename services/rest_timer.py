"""
Rest timer service.
Sends a countdown message after each set, fires alert when rest is over.
Uses asyncio background task — no APScheduler needed.
"""
import asyncio
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

REST_SECONDS = 90


def _rest_kb(se_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="➡️ Следующий подход", callback_data=ff"rest:next:{se_id}:{next_set}"),
        InlineKeyboardButton(text="⏭ Пропустить отдых", callback_data=ff"rest:skip:{se_id}:{next_set}"),
    ]])


async def run_rest_timer(bot: Bot, chat_id: int, se_id: int, next_set: int, seconds: int = REST_SECONDS) -> None:
    """Fire-and-forget: send rest message, count down, then alert user."""
    msg = await bot.send_message(
        chat_id,
        f"⏱ Отдых <b>{seconds} сек</b>\n\nНажми когда будешь готов.",
        parse_mode="HTML",
        reply_markup=_rest_kb(se_id),
    )
    remaining = seconds
    while remaining > 0:
        await asyncio.sleep(min(30, remaining))
        remaining = max(0, remaining - 30)
        try:
            text = (
                "🔔 <b>Отдых завершён!</b> Время следующего подхода 💪"
                if remaining == 0
                else f"⏱ Осталось <b>{remaining} сек</b>"
            )
            await bot.edit_message_text(
                text,
                chat_id=chat_id,
                message_id=msg.message_id,
                parse_mode="HTML",
                reply_markup=_rest_kb(se_id),
            )
        except Exception:
            pass
