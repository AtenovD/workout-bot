<p align="center">
  <img src="assets/architecture-banner.svg" alt="Workout Bot architecture overview" width="100%">
</p>

# 🏋️ Workout Bot — Personal AI Trainer for Telegram

A Telegram bot for strength training with adaptive workout planning, gamification, and progress tracking.

<p align="center">
  <img src="assets/chat-preview.svg" alt="Workout Bot chat preview" width="100%">
</p>

## ✨ Features

<p align="center">
  <img src="assets/feature-map.svg" alt="Workout Bot feature map" width="100%">
</p>

- **Onboarding** — 12-step profile calibration (goal, experience, equipment, health), fully localized (🇷🇺/🇬🇧)
- **Workout generator** — adaptive exercise selection based on profile and available equipment
- **Set logging** — reps, weights, adjustments, difficulty modifiers
- **Progressive overload** — automatic calculation of the next weight
- **AI coach** — Groq-powered review of logged sessions
- **Channel subscription gate** — optional required-channel check before using the bot, RU/EN aware
- **Stats** — volume, calories, streaks, personal records
- **Charts** — progress visualization via matplotlib
- **Achievements** — 25+ badges with XP rewards

<p align="center">
  <img src="assets/gamification-diagram.svg" alt="Workout Bot gamification loop" width="100%">
</p>

- **Gamification** — levels, XP, titles (Beginner → Gym God)
- **Schedule** — fixed/spontaneous mode with reminders
- **Body measurement tracking** — body weight, body fat percentage

## 🏗 Stack

| Component | Technology |
|-----------|-----------|
| Bot       | aiogram 3.7 |
| Web API   | FastAPI + uvicorn |
| Database  | PostgreSQL 15 + SQLAlchemy 2.0 async |
| Cache     | Redis 7 |
| Storage   | MinIO (S3-compatible) |
| AI        | Groq (OpenAI-compatible API) |
| Migrations| Alembic |
| Charts    | Matplotlib |
| Deploy    | Docker Compose |

## 🚀 Quick start

```bash
# Clone the repository
git clone https://github.com/AtenovD/workout-bot.git
cd workout-bot

# Copy the config
cp .env.example .env
# Fill in BOT_TOKEN, passwords, and GROQ_API_KEY in .env

# Start
docker-compose up -d

# Apply migrations
docker-compose exec bot alembic upgrade head

# Seed the database with exercises and achievements
docker-compose exec bot python -m scripts.seed_data
```

## 📁 Project structure

```
workout-bot/
├── bot/
│   ├── handlers/          # Telegram handlers
│   │   ├── onboarding.py  # /start, onboarding & calibration
│   │   ├── workout.py     # Workout flow
│   │   ├── progress.py    # Progress + charts
│   │   ├── stats.py       # Stats
│   │   ├── profile.py     # User profile
│   │   ├── achievements.py# Achievements
│   │   └── schedule.py    # Schedule
│   ├── keyboards/         # InlineKeyboard factories
│   ├── middlewares/       # DB + User middlewares
│   ├── states/            # FSM states
│   ├── texts/             # RU/EN string dictionaries
│   └── main.py            # Entry point
├── models/                # SQLAlchemy models
├── services/               # Business logic
│   ├── workout_generator.py
│   ├── progression.py
│   ├── gamification.py
│   ├── calories.py
│   ├── achievement_checker.py
│   ├── stats_chart.py
│   └── reminder.py
├── core/                  # Config + DB
├── migrations/            # Alembic migrations
├── scripts/                # Seed data
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## ⚙️ Environment variables

See `.env.example` for the full list.

| Variable | Description |
|-----------|---------|
| BOT_TOKEN | Telegram bot token (@BotFather) |
| DATABASE_URL | PostgreSQL connection string |
| REDIS_URL | Redis connection string |
| ADMIN_IDS | Comma-separated Telegram admin IDs |
| GROQ_API_KEY | Groq API key for the AI coach feature |

## 📊 Architecture

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

## 🎮 Bot commands

| Command | Description |
|---------|---------|
| /start | Registration / onboarding |
| /workout | Start a workout |
| /progress | Progress and charts |
| /stats | Stats |
| /achievements | Achievements |
| /profile | Profile |
| /schedule | Schedule |
| /menu | Main menu |

## Note on language

Onboarding, the main workout flow, and the subscription gate are localized RU/EN through `bot/texts/`. Some deeper screens (profile details, some admin/reporting text) and the exercise coaching content (instructions/tips/common mistakes) are still Russian-only — translating those is tracked as follow-up work.

## License

MIT — see [LICENSE](LICENSE).
