"""
Seed script: populates muscle groups, equipment catalog, exercises, and achievements.
Run: python -m scripts.seed_data
"""
import asyncio
from core.db import AsyncSessionLocal, engine, Base
from models.exercise import Equipment, MuscleGroup, Exercise, EquipmentCategory, ExerciseType
from models.gamification import Achievement, AchievementCategory, AchievementTier


MUSCLE_GROUPS = [
    {"code": "chest",      "name_ru": "Грудь",        "name_en": "Chest",       "body_part": "upper"},
    {"code": "back",       "name_ru": "Спина",        "name_en": "Back",        "body_part": "upper"},
    {"code": "shoulders",  "name_ru": "Плечи",        "name_en": "Shoulders",   "body_part": "upper"},
    {"code": "biceps",     "name_ru": "Бицепс",       "name_en": "Biceps",      "body_part": "upper"},
    {"code": "triceps",    "name_ru": "Трицепс",      "name_en": "Triceps",     "body_part": "upper"},
    {"code": "forearms",   "name_ru": "Предплечья",   "name_en": "Forearms",    "body_part": "upper"},
    {"code": "quads",      "name_ru": "Квадрицепс",   "name_en": "Quads",       "body_part": "lower"},
    {"code": "hamstrings", "name_ru": "Бицепс бедра", "name_en": "Hamstrings",  "body_part": "lower"},
    {"code": "glutes",     "name_ru": "Ягодицы",      "name_en": "Glutes",      "body_part": "lower"},
    {"code": "calves",     "name_ru": "Икры",         "name_en": "Calves",      "body_part": "lower"},
    {"code": "core",       "name_ru": "Кор / Пресс",  "name_en": "Core",        "body_part": "core"},
    {"code": "traps",      "name_ru": "Трапеции",     "name_en": "Traps",       "body_part": "upper"},
    {"code": "lats",       "name_ru": "Широчайшие",   "name_en": "Lats",        "body_part": "upper"},
    {"code": "fullbody",   "name_ru": "Всё тело",     "name_en": "Full Body",   "body_part": "fullbody"},
]

EQUIPMENT_CATALOG = [
    # None category
    {"code": "bodyweight",    "name_ru": "Собственный вес", "name_en": "Bodyweight",    "category": "none",       "icon": "🤸"},
    # Portable
    {"code": "dumbbells",     "name_ru": "Гантели",         "name_en": "Dumbbells",     "category": "portable",   "icon": "🏋️"},
    {"code": "barbell",       "name_ru": "Штанга",          "name_en": "Barbell",       "category": "portable",   "icon": "🏋️"},
    {"code": "kettlebell",    "name_ru": "Гиря",            "name_en": "Kettlebell",    "category": "portable",   "icon": "⚫"},
    {"code": "resistance_band","name_ru": "Резинка",         "name_en": "Resistance Band","category": "portable",  "icon": "🔴"},
    {"code": "pull_up_bar",   "name_ru": "Турник",          "name_en": "Pull-up Bar",   "category": "portable",   "icon": "🔩"},
    {"code": "jump_rope",     "name_ru": "Скакалка",        "name_en": "Jump Rope",     "category": "portable",   "icon": "⭕"},
    {"code": "bench",         "name_ru": "Скамья",          "name_en": "Bench",         "category": "portable",   "icon": "🪑"},
    {"code": "trx",           "name_ru": "TRX петли",       "name_en": "TRX",           "category": "portable",   "icon": "🔗"},
    {"code": "fitball",       "name_ru": "Фитбол",          "name_en": "Fitball",       "category": "portable",   "icon": "🏀"},
    {"code": "dip_bars",      "name_ru": "Брусья",          "name_en": "Dip Bars",      "category": "portable",   "icon": "🤸"},
    # Stationary
    {"code": "cable_machine",  "name_ru": "Блочный тренажёр", "name_en": "Cable Machine",   "category": "stationary", "icon": "🏗"},
    {"code": "leg_press",      "name_ru": "Жим ногами",       "name_en": "Leg Press",       "category": "stationary", "icon": "🦵"},
    {"code": "smith_machine",  "name_ru": "Смит",             "name_en": "Smith Machine",   "category": "stationary", "icon": "🏋️"},
    {"code": "lat_pulldown",   "name_ru": "Верхний блок",     "name_en": "Lat Pulldown",    "category": "stationary", "icon": "🔽"},
    {"code": "seated_row",     "name_ru": "Нижний блок",      "name_en": "Seated Row",      "category": "stationary", "icon": "🚣"},
    {"code": "chest_press_machine","name_ru": "Тренажёр жим грудь","name_en": "Chest Press","category": "stationary", "icon": "💪"},
    {"code": "shoulder_press_machine","name_ru": "Тренажёр жим плечи","name_en": "Shoulder Press","category": "stationary","icon": "🔝"},
    {"code": "leg_curl",       "name_ru": "Сгибание ног",     "name_en": "Leg Curl",        "category": "stationary", "icon": "🦵"},
    {"code": "leg_extension",  "name_ru": "Разгибание ног",   "name_en": "Leg Extension",   "category": "stationary", "icon": "🦵"},
    {"code": "crossover",      "name_ru": "Кроссовер",        "name_en": "Crossover",       "category": "stationary", "icon": "✖️"},
    {"code": "hack_squat",     "name_ru": "Гак-присед",       "name_en": "Hack Squat",      "category": "stationary", "icon": "🦵"},
    {"code": "calf_raise_machine","name_ru": "Тренажёр икры", "name_en": "Calf Raise",      "category": "stationary", "icon": "🦵"},
    {"code": "pec_deck",       "name_ru": "Бабочка",          "name_en": "Pec Deck",        "category": "stationary", "icon": "🦋"},
    {"code": "rowing_machine", "name_ru": "Гребной тренажёр", "name_en": "Rowing Machine",  "category": "stationary", "icon": "🚣"},
    {"code": "treadmill",      "name_ru": "Беговая дорожка",  "name_en": "Treadmill",       "category": "stationary", "icon": "🏃"},
    {"code": "stationary_bike","name_ru": "Велотренажёр",     "name_en": "Stationary Bike", "category": "stationary", "icon": "🚴"},
    {"code": "elliptical",     "name_ru": "Эллипсоид",        "name_en": "Elliptical",      "category": "stationary", "icon": "⭕"},
]

ACHIEVEMENTS = [
    # Consistency
    {"code": "first_workout",    "name": "Первый шаг",         "description": "Завершил первую тренировку",         "icon": "👟", "category": "consistency", "tier": "bronze",   "xp_reward": 50,  "condition": {"type": "total_workouts", "value": 1}},
    {"code": "workouts_7",       "name": "Неделя силы",         "description": "7 тренировок выполнено",             "icon": "📅", "category": "consistency", "tier": "bronze",   "xp_reward": 100, "condition": {"type": "total_workouts", "value": 7}},
    {"code": "workouts_30",      "name": "Месяц в зале",        "description": "30 тренировок выполнено",            "icon": "🏅", "category": "consistency", "tier": "silver",   "xp_reward": 300, "condition": {"type": "total_workouts", "value": 30}},
    {"code": "workouts_100",     "name": "Сотка",               "description": "100 тренировок выполнено",           "icon": "💯", "category": "consistency", "tier": "gold",     "xp_reward": 1000,"condition": {"type": "total_workouts", "value": 100}},
    {"code": "streak_7",         "name": "Огонь 🔥",           "description": "7 тренировок подряд без пропусков",  "icon": "🔥", "category": "consistency", "tier": "silver",   "xp_reward": 200, "condition": {"type": "streak", "value": 7}},
    {"code": "streak_30",        "name": "Несгораемый",         "description": "30 дней подряд",                    "icon": "⚡", "category": "consistency", "tier": "gold",     "xp_reward": 500, "condition": {"type": "streak", "value": 30}},
    {"code": "no_skip_month",    "name": "Без пропусков",       "description": "Ни одного пропуска за месяц",       "icon": "✅", "category": "consistency", "tier": "gold",     "xp_reward": 400, "condition": {"type": "no_skip_days", "value": 30}},
    # Strength
    {"code": "pr_first",         "name": "Новый рекорд!",       "description": "Установил первый личный рекорд",    "icon": "🥇", "category": "strength",     "tier": "bronze",   "xp_reward": 75,  "condition": {"type": "pr_count", "value": 1}},
    {"code": "pr_10",            "name": "Рекордсмен",          "description": "10 личных рекордов",                "icon": "🏆", "category": "strength",     "tier": "silver",   "xp_reward": 250, "condition": {"type": "pr_count", "value": 10}},
    {"code": "bench_bodyweight", "name": "Жим своего веса",     "description": "Жим лёжа = свой вес",              "icon": "🎯", "category": "strength",     "tier": "gold",     "xp_reward": 500, "condition": {"type": "exercise_ratio", "exercise": "bench_press", "ratio": 1.0}},
    {"code": "squat_1_5x",       "name": "Приседание 1.5x",     "description": "Присед = 1.5× своего веса",        "icon": "🦵", "category": "strength",     "tier": "gold",     "xp_reward": 500, "condition": {"type": "exercise_ratio", "exercise": "squat", "ratio": 1.5}},
    # Volume
    {"code": "volume_1t",        "name": "Тонна за тренировку", "description": "1 000 кг за одну тренировку",      "icon": "💪", "category": "volume",       "tier": "silver",   "xp_reward": 200, "condition": {"type": "session_volume", "value": 1000}},
    {"code": "volume_10t",       "name": "Атлет",               "description": "10 тонн за тренировку",            "icon": "💥", "category": "volume",       "tier": "gold",     "xp_reward": 500, "condition": {"type": "session_volume", "value": 10000}},
    {"code": "total_100t",       "name": "100 тонн",            "description": "100 тонн суммарно",                "icon": "🏋️", "category": "volume",       "tier": "silver",   "xp_reward": 300, "condition": {"type": "total_volume", "value": 100000}},
    {"code": "total_1000t",      "name": "Машина",              "description": "1 000 тонн суммарно",              "icon": "🤖", "category": "volume",       "tier": "platinum", "xp_reward": 2000,"condition": {"type": "total_volume", "value": 1000000}},
    # Milestone
    {"code": "goal_weight",      "name": "Цель достигнута!",    "description": "Достиг целевого веса",             "icon": "🎯", "category": "milestone",    "tier": "gold",     "xp_reward": 1000,"condition": {"type": "reached_target_weight"}},
    {"code": "weight_minus_5",   "name": "-5 кг",               "description": "Сбросил 5 кг от начального веса", "icon": "📉", "category": "milestone",    "tier": "silver",   "xp_reward": 300, "condition": {"type": "weight_loss", "value": 5}},
    {"code": "weight_plus_5",    "name": "+5 кг массы",         "description": "Набрал 5 кг от начального веса",  "icon": "📈", "category": "milestone",    "tier": "silver",   "xp_reward": 300, "condition": {"type": "weight_gain", "value": 5}},
    {"code": "level_10",         "name": "Атлет",               "description": "Достиг 10-го уровня",             "icon": "⭐", "category": "milestone",    "tier": "gold",     "xp_reward": 500, "condition": {"type": "level", "value": 10}},
    # Special
    {"code": "early_bird",       "name": "Ранняя пташка",       "description": "Тренировка до 7 утра",            "icon": "🌅", "category": "special",      "tier": "bronze",   "xp_reward": 100, "condition": {"type": "workout_before_hour", "value": 7}},
    {"code": "night_owl",        "name": "Сова",                "description": "Тренировка после 22:00",          "icon": "🦉", "category": "special",      "tier": "bronze",   "xp_reward": 100, "condition": {"type": "workout_after_hour", "value": 22}},
    {"code": "weekend_warrior",  "name": "Воин выходного дня",  "description": "5 тренировок в выходные",        "icon": "🗓", "category": "special",      "tier": "bronze",   "xp_reward": 150, "condition": {"type": "weekend_workouts", "value": 5}},
    {"code": "hard_mode_10",     "name": "Мазохист",            "description": "10 тренировок в режиме 🔴",      "icon": "🔴", "category": "special",      "tier": "silver",   "xp_reward": 200, "condition": {"type": "hard_sessions", "value": 10}},
    {"code": "comeback",         "name": "Камбэк",              "description": "Вернулся после 2+ недель перерыва","icon": "🔙", "category": "special",      "tier": "bronze",   "xp_reward": 75,  "condition": {"type": "return_after_days", "value": 14}},
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Seed muscle groups
        for mg_data in MUSCLE_GROUPS:
            mg = MuscleGroup(**mg_data)
            session.add(mg)

        # Seed equipment
        eq_map = {}
        for eq_data in EQUIPMENT_CATALOG:
            eq = Equipment(**{k: v for k, v in eq_data.items()})
            session.add(eq)

        # Seed achievements
        for ach_data in ACHIEVEMENTS:
            ach = Achievement(
                code=ach_data["code"],
                name=ach_data["name"],
                description=ach_data["description"],
                icon=ach_data.get("icon"),
                category=AchievementCategory(ach_data["category"]),
                tier=AchievementTier(ach_data["tier"]),
                xp_reward=ach_data["xp_reward"],
                condition=ach_data["condition"],
            )
            session.add(ach)

        await session.commit()
        print("✅ Seed data inserted: muscle groups, equipment, achievements")
        print("📝 TODO: Add exercises with photos (80-120 exercises for MVP)")


if __name__ == "__main__":
    asyncio.run(seed())
