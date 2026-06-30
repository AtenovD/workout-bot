ADMIN_IDS: set[int] = set()


def set_admins(ids) -> None:
    ADMIN_IDS.clear()
    ADMIN_IDS.update(int(admin_id) for admin_id in ids)


def is_admin_telegram_id(telegram_id: int | None) -> bool:
    return bool(telegram_id and telegram_id in ADMIN_IDS)
