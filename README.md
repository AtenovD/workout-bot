# 🏋️ Workout Bot — Персональный AI-тренер для Telegram

Интеллектуальный Telegram-бот для силовых тренировок с адаптивным планированием, геймификацией и трекингом прогресса.

## ✨ Функционал

- **Онбординг** — 12-шаговая калибровка профиля (цель, опыт, оборудование, здоровье)
- **Генератор тренировок** — адаптивный подбор упражнений на основе профиля и оборудования
- **Логирование сетов** — подходы, веса, корректировки, модификаторы сложности
- **Прогрессивная нагрузка** — автоматический расчёт следующего веса
- **Статистика** — объём, калории, стрики, личные рекорды
- **Графики** — визуализация прогресса через matplotlib
- **Достижения** — 25+ ачивок с XP-вознаграждениями
- **Геймификация** — уровни, XP, титулы (Новичок → Бог зала)
- **Расписание** — фиксированный/спонтанный режим с напоминаниями
- **Трекинг замеров** — вес тела, жировой процент

## 🏗 Стек

| Компонент | Технология |
|-----------|-----------|
| Bot       | aiogram 3.7 |
| Web API   | FastAPI + uvicorn |
| Database  | PostgreSQL 15 + SQLAlchemy 2.0 async |
| Cache     | Redis 7 |
| Storage   | MinIO (S3-compatible) |
| Migrations| Alembic |
| Charts    | Matplotlib |
| Deploy    | Docker Compose |

## 🚀 Быстрый старт

```bash
# Клонировать репозиторий
git clone https://github.com/AtenovD/workout-bot.git
cd workout-bot

# Скопировать конфиг
cp .env.example .env
# Заполнить BOT_TOKEN и пароли в .env

# Запустить
docker-compose up -d

# Применить миграции
docker-compose exec bot alembic upgrade head

# Наполнить базу данными упражнений и достижений
docker-compose exec bot python -m scripts.seed_data
```

## 📁 Структура проекта

```
workout-bot/
├── bot/
│   ├── handlers/          # Telegram handlers
│   │   ├── start.py       # /start, онбординг
│   │   ├── workout.py     # Тренировочный процесс
│   │   ├── progress.py    # Прогресс + графики
│   │   ├── stats.py       # Статистика
│   │   ├── profile.py     # Профиль пользователя
│   │   ├── achievements.py# Достижения
│   │   └── schedule.py    # Расписание
│   ├── keyboards/         # InlineKeyboard factories
│   ├── middlewares/       # DB + User middlewares
│   ├── states/            # FSM states
│   └── main.py            # Entry point
├── models/                # SQLAlchemy models
├── services/              # Business logic
│   ├── workout_generator.py
│   ├── progression.py
│   ├── gamification.py
│   ├── calories.py
│   ├── achievement_checker.py
│   ├── stats_chart.py
│   └── reminder.py
├── core/                  # Config + DB
├── migrations/            # Alembic migrations
├── scripts/               # Seed data
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## ⚙️ Переменные окружения

Смотри `.env.example` для полного списка.

| Переменная | Описание |
|-----------|---------|
| BOT_TOKEN | Токен Telegram бота (@BotFather) |
| DATABASE_URL | PostgreSQL connection string |
| REDIS_URL | Redis connection string |
| ADMIN_IDS | Telegram IDs администраторов через запятую |

## 📊 Архитектура

```
Telegram User
     │
     ▼
aiogram Dispatcher
     │
     ├── DbSessionMiddleware (injects AsyncSession)
     ├── UserMiddleware (creates/fetches User record)
     │
     ├── Handlers (Router)
     │     └── Services (business logic)
     │           └── Models (SQLAlchemy ORM)
     │                 └── PostgreSQL
     │
     └── FSM Storage → Redis
```

## 🎮 Команды бота

| Команда | Описание |
|---------|---------|
| /start | Регистрация / онбординг |
| /workout | Начать тренировку |
| /progress | Прогресс и графики |
| /stats | Статистика |
| /achievements | Достижения |
| /profile | Профиль |
| /schedule | Расписание |
| /menu | Главное меню |
