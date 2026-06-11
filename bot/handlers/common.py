from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from bot.keyboards.main_menu import main_menu_keyboard

router = Router()


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    await message.answer(
        "🏠 <b>Главное меню</b>\n\nВыбери раздел:",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "ℹ️ <b>Помощь</b>\n\n"
        "/start — Начать / пройти калибровку\n"
        "/workout — Начать тренировку\n"
        "/progress — Прогресс и статистика\n"
        "/menu — Главное меню\n"
        "/settings — Настройки\n\n"
        "По вопросам: @support"
    )
    await message.answer(text, parse_mode="HTML")


@router.message()
async def fallback(message: Message):
    await message.answer("Используй /menu для навигации или /help для справки.")
