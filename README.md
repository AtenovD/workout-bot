# 🏋️ Workout Bot — Персональный AI-тренер

Telegram-бот, который полностью заменяет персонального тренера: проводит калибровку, генерирует адаптивные тренировки под доступный инвентарь, ведёт прогресс и мотивирует геймификацией.

## Технологический стек

- **Python 3.11+** + **aiogram 3.x** — async bot framework, FSM
- **FastAPI** — REST API, вебхуки, админ-панель
- **PostgreSQL 15+** + **SQLAlchemy 2.0 async** + **Alembic**
- **Redis 7** — FSM-storage, кэш, rate-limit
- **APScheduler** — напоминания и фоновые задачи
- **MinIO (S3)** — хранилище медиа
- **matplotlib/Pillow** — графики прогресса
- **Docker + docker-compose** — деплой на VPS

## Быстрый старт

```bash
git clone https://github.com/AtenovD/workout-bot.git
cd workout-bot
cp .env.example .env
# Заполни .env своими данными
docker-compose up -d
docker-compose exec bot alembic upgrade head
docker-compose exec bot python -m scripts.seed_data
```

## Структура проекта

```
fitness_bot/
├── bot/
│   ├── main.py
│   ├── handlers/
│   ├── keyboards/
│   ├── states/
│   ├── middlewares/
│   └── texts/
├── core/
├── models/
├── repositories/
├── services/
├── api/
├── workers/
├── migrations/
├── scripts/
└── tests/
```

## Фазы разработки

- **MVP:** Калибровка → Инвентарь → Генератор тренировки → Прогрессия
- **Фаза 2:** Расписание, напоминания, геймификация, графики
- **Фаза 3:** Аналитика, репост-карточки, лидерборд, админка
- **Фаза 4:** Авто-дилоад, питание, Mini App
