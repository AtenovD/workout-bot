import pytest
from aiogram.exceptions import TelegramBadRequest

from bot.utils.message_edit import safe_edit_text


class _FakeMessage:
    def __init__(self):
        self.answered = None

    async def edit_text(self, text, **kwargs):
        raise TelegramBadRequest(method="editMessageText", message="Bad Request: message can't be edited")

    async def answer(self, text, **kwargs):
        self.answered = (text, kwargs)
        return self.answered


@pytest.mark.asyncio
async def test_safe_edit_text_answers_when_message_cannot_be_edited():
    message = _FakeMessage()

    result = await safe_edit_text(message, "done", parse_mode="HTML")

    assert result == ("done", {"parse_mode": "HTML"})
    assert message.answered == ("done", {"parse_mode": "HTML"})
