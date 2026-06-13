from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from datetime import datetime, date

from bot.keyboards.main_menu import main_menu_keyboard
from models.user import User
from models.challenge import UserChallenge
from models.gamification import UserStats

router = Router()

CHALLENGE_DAYS = 30
CHALLENGE_XP_REWARD = 500


@router.message(Command("challenge"))
async def show_challenge(message: Message, user: User, session: AsyncSession):
    challenge = await session.execute(
        select(UserChallenge).where(UserChallenge.user_id == user.id)
    )
    challenge = challenge.scalar_one_or_none()

    if not challenge:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔥 Присоединиться к челленджу", callback_data="challenge:join")]
        ])
        await message.answer(
            "🏆 <b>30-дневный челлендж</b>\n\n"
            "Тренируйся каждый день в течение 30 дней и получи особую награду!\n\n"
            f"🎁 Награда: <b>{CHALLENGE_XP_REWARD} XP</b> + уникальный титул\n"
            "📋 Правила: минимум 1 завершённая тренировка в день",
            reply_markup=kb,
            parse_mode="HTML"
        )
        return

    done = len(challenge.workout_days or [])
    progress_pct = min(done * 100 // CHALLENGE_DAYS, 100)
    bar_len = 15
    filled = int(bar_len * progress_pct / 100)
    bar = "█" * filled + "░" * (bar_len - filled)

    if challenge.completed:
        status = "✅ <b>Челлендж завершён!</b>"
    else:
        status = f"🔥 День <b>{challenge.current_day}</b> из <b>{CHALLENGE_DAYS}</b>"

    await message.answer(
        f"🏆 <b>30-дневный челлендж</b>\n\n"
        f"{status}\n"
        f"[{bar}] {progress_pct}%\n\n"
        f"📅 Дней тренировок: <b>{done}</b>\n"
        f"🎁 Награда: <b>{CHALLENGE_XP_REWARD} XP</b>\n\n"
        f"{'🥳 Поздравляем с завершением!' if challenge.completed else 'Продолжай в том же духе! 💪'}",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "challenge:join")
async def join_challenge(callback: CallbackQuery, user: User, session: AsyncSession):
    existing = await session.execute(
        select(UserChallenge).where(UserChallenge.user_id == user.id)
    )
    if existing.scalar_one_or_none():
        await callback.answer("Ты уже в челлендже!", show_alert=True)
        return

    challenge = UserChallenge(
        user_id=user.id,
        current_day=0,
        workout_days=[],
        completed=False,
    )
    session.add(challenge)
    await session.commit()

    await callback.message.edit_text(
        "🔥 <b>Ты в игре!</b>\n\n"
        "30-дневный челлендж активирован.\n"
        "Каждая завершённая тренировка приближает тебя к цели.\n\n"
        "Используй /challenge чтобы следить за прогрессом.",
        parse_mode="HTML"
    )
    await callback.answer("🔥 Челлендж активирован!")


@router.callback_query(F.data == "menu:challenge")
async def challenge_from_menu(callback: CallbackQuery, user: User, session: AsyncSession):
    challenge = await session.execute(
        select(UserChallenge).where(UserChallenge.user_id == user.id)
    )
    challenge = challenge.scalar_one_or_none()

    if not challenge:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔥 Присоединиться", callback_data="challenge:join")],
            [InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:main")],
        ])
        await callback.message.edit_text(
            "🏆 <b>30-дневный челлендж</b>\n\n"
            "Тренируйся 30 дней подряд и получи:\n"
            f"🎁 <b>{CHALLENGE_XP_REWARD} XP</b>\n"
            "🏅 Уникальный титул «Железный»",
            reply_markup=kb,
            parse_mode="HTML"
        )
        return

    done = len(challenge.workout_days or [])
    progress_pct = min(done * 100 // CHALLENGE_DAYS, 100)
    bar_len = 12
    filled = int(bar_len * progress_pct / 100)
    bar = "█" * filled + "░" * (bar_len - filled)

    if challenge.completed:
        status = "✅ Завершён!"
    else:
        status = f"🔥 День {challenge.current_day}/{CHALLENGE_DAYS}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:main")],
    ])

    await callback.message.edit_text(
        f"🏆 <b>30-дневный челлендж</b>\n\n"
        f"{status}\n"
        f"[{bar}] {progress_pct}%\n\n"
        f"📅 Тренировок: <b>{done}</b> из <b>{CHALLENGE_DAYS}</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )
