import re
from pathlib import Path


BOT_ROOT = Path(__file__).resolve().parents[1] / "bot"


def _python_files():
    return list(BOT_ROOT.rglob("*.py"))


def test_static_callback_buttons_have_handlers():
    buttons = []
    handlers = []

    for path in _python_files():
        source = path.read_text(encoding="utf-8-sig")
        for match in re.finditer(r"callback_data\s*=\s*f?[\"']([^\"']+)", source):
            buttons.append((match.group(1), path))
        for match in re.finditer(r"F\.data\s*==\s*[\"']([^\"']+)", source):
            handlers.append(("eq", match.group(1)))
        for match in re.finditer(r"F\.data\.startswith\([\"']([^\"']+)", source):
            handlers.append(("prefix", match.group(1)))

    unmatched = []
    for callback_data, path in sorted(set(buttons)):
        if "{" in callback_data:
            callback_data = callback_data.split("{", 1)[0]
        if not callback_data:
            continue
        matched = any(
            (kind == "eq" and callback_data == value)
            or (kind == "prefix" and callback_data.startswith(value))
            for kind, value in handlers
        )
        if not matched:
            unmatched.append(f"{callback_data} in {path.relative_to(BOT_ROOT.parent)}")

    assert unmatched == []


def test_handlers_use_safe_text_editing():
    offenders = []
    for path in (BOT_ROOT / "handlers").glob("*.py"):
        source = path.read_text(encoding="utf-8-sig")
        if ".edit_text(" in source:
            offenders.append(str(path.relative_to(BOT_ROOT.parent)))

    assert offenders == []
