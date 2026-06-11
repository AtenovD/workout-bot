from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏋️ Тренировка", callback_data="menu:workout")],
        [
            InlineKeyboardButton(text="📅 Расписание", callback_data="menu:schedule"),
            InlineKeyboardButton(text="📊 Прогресс", callback_data="menu:progress"),
        ],
        [
            InlineKeyboardButton(text="🎒 Инвентарь", callback_data="menu:equipment"),
            InlineKeyboardButton(text="🏆 Достижения", callback_data="menu:achievements"),
        ],
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="menu:profile"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu:settings"),
        ],
    ])


def workout_modifier_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Облегчённый", callback_data="modifier:light")],
        [InlineKeyboardButton(text="⚪ Обычный", callback_data="modifier:normal")],
        [InlineKeyboardButton(text="🔴 Утяжелённый", callback_data="modifier:hard")],
    ])


def set_logging_keyboard(set_num: int, target_reps: int) -> InlineKeyboardMarkup:
    reps_row = [
        InlineKeyboardButton(text="−", callback_data=f"reps:minus"),
        InlineKeyboardButton(text=f"{target_reps} повт.", callback_data="reps:current"),
        InlineKeyboardButton(text="+", callback_data=f"reps:plus"),
    ]
    return InlineKeyboardMarkup(inline_keyboard=[
        reps_row,
        [InlineKeyboardButton(text=f"✅ Подход {set_num} выполнен", callback_data="set:done")],
        [
            InlineKeyboardButton(text="😰 Слишком тяжело", callback_data="weight:decrease"),
            InlineKeyboardButton(text="😊 Слишком легко", callback_data="weight:increase"),
        ],
        [
            InlineKeyboardButton(text="🔄 Заменить упражнение", callback_data="exercise:replace"),
            InlineKeyboardButton(text="⏭ Пропустить", callback_data="exercise:skip"),
        ],
    ])
