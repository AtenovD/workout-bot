from pathlib import Path

from aiogram.types import CallbackQuery, FSInputFile, Message


ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets" / "modules"

MODULE_IMAGES = {
    "workout": "workout.png",
    "progress": "progress.png",
    "achievements": "achievements.png",
    "calibration": "calibration.png",
    "schedule": "schedule.png",
    "challenge": "challenge.png",
    "inventory": "inventory.png",
    "settings": "settings.png",
}


async def send_module_visual(
    event: Message | CallbackQuery,
    module: str,
    caption: str,
    *,
    reply_markup=None,
    parse_mode: str = "HTML",
) -> None:
    image_name = MODULE_IMAGES[module]
    photo = FSInputFile(ASSETS_DIR / image_name)
    can_use_caption = len(caption) <= 1000

    if isinstance(event, CallbackQuery):
        if not can_use_caption:
            await event.message.answer_photo(photo)
            await event.message.answer(caption, reply_markup=reply_markup, parse_mode=parse_mode)
            await event.answer()
            return

        await event.message.answer_photo(
            photo,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
        await event.answer()
        return

    if not can_use_caption:
        await event.answer_photo(photo)
        await event.answer(caption, reply_markup=reply_markup, parse_mode=parse_mode)
        return

    await event.answer_photo(
        photo,
        caption=caption,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
    )
