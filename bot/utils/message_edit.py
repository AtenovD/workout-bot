from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message


async def safe_edit_text(message: Message, text: str, **kwargs):
    try:
        return await message.edit_text(text, **kwargs)
    except TelegramBadRequest as exc:
        error_text = str(exc).lower()
        if "message is not modified" in error_text:
            return None
        if "no text in the message to edit" in error_text or "message is not a text message" in error_text:
            try:
                return await message.edit_caption(caption=text, **kwargs)
            except TelegramBadRequest as caption_exc:
                caption_error = str(caption_exc).lower()
                if "message is not modified" in caption_error:
                    return None
            return await message.answer(text, **kwargs)
        raise
