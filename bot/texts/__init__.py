# bot/texts/__init__.py
from bot.texts.ru import TEXTS as RU_TEXTS
from bot.texts.en import TEXTS as EN_TEXTS

_TEXTS = {"ru": RU_TEXTS, "en": EN_TEXTS}


def t(key: str, lang: str = "ru", **kwargs) -> str:
    texts = _TEXTS.get(lang, RU_TEXTS)
    text = texts.get(key, RU_TEXTS.get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
