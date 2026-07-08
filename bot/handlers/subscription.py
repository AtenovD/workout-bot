from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.main_menu import admin_reply_keyboard, main_menu_keyboard
from bot.services.admin_access import is_admin_telegram_id
from bot.services.subscription_gate import (
    get_required_en_channel,
    has_required_subscription,
    subscription_gate_markup,
    subscription_gate_text,
)
from bot.states.states import OnboardingStates
from bot.texts import t
from bot.utils.message_edit import safe_edit_text
from models.profile import Profile
from models.user import User

router = Router()


def _onboarding_welcome_text(first_name: str) -> str:
    return (
        f"👋 <b>Hi, {first_name}!</b>\n\n"
        "I am your <b>personal AI coach</b>. I will:\n"
        "• Build workouts strictly around your inventory\n"
        "• Guide you exercise by exercise with visuals\n"
        "• Track progress and adjust load automatically\n"
        "• Motivate you with XP, levels, and achievements\n\n"
        "Let's run a quick calibration - about 2 minutes 🚀"
    )


def _start_calibration_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🚀 Let's go!", callback_data="cal:start")]]
    )


@router.callback_query(F.data == "sub:check")
async def check_subscription(callback: CallbackQuery, state: FSMContext, user: User, session: AsyncSession):
    if not await has_required_subscription(callback.bot, session, user):
        channel = await get_required_en_channel(session)
        if channel:
            await safe_edit_text(
                callback.message,
                subscription_gate_text(channel),
                reply_markup=subscription_gate_markup(channel),
                parse_mode="HTML",
            )
        await callback.answer("Subscription was not found yet. Subscribe and try again.", show_alert=True)
        return

    await callback.answer("Subscription confirmed.")
    result = await session.execute(select(Profile).where(Profile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if profile and profile.calibrated_at:
        text = t("main_menu_title", "en")
        reply_markup = (
            admin_reply_keyboard("en")
            if is_admin_telegram_id(user.telegram_id)
            else main_menu_keyboard(lang="en", telegram_id=user.telegram_id)
        )
        if is_admin_telegram_id(user.telegram_id):
            await callback.message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await safe_edit_text(callback.message, text, reply_markup=reply_markup, parse_mode="HTML")
        return

    await state.set_state(OnboardingStates.welcome)
    await state.update_data(language="en")
    await safe_edit_text(
        callback.message,
        _onboarding_welcome_text(callback.from_user.first_name),
        reply_markup=_start_calibration_kb(),
        parse_mode="HTML",
    )
