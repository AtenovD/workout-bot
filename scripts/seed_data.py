"""
Seed script — combines all exercise data and populates all reference tables.
Run: python -m scripts.seed_data
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from core.db import AsyncSessionLocal, engine, Base
from models.exercise import Equipment, MuscleGroup, Exercise, EquipmentCategory, ExerciseType
from models.gamification import Achievement, AchievementCategory, AchievementTier
from scripts.exercises_chest_back import EXERCISES_CHEST_BACK
from scripts.exercises_rest import EXERCISES_REST

EXERCISES = EXERCISES_CHEST_BACK + EXERCISES_REST

MUSCLE_GROUPS = [
    {"code": "chest",      "name_ru": "Грудь",        "name_en": "Chest",      "body_part": "upper"},
    {"code": "back",       "name_ru": "Спина",        "name_en": "Back",       "body_part": "upper"},
    {"code": "lats",       "name_ru": "Широчайшие",   "name_en": "Lats",       "body_part": "upper"},
    {"code": "traps",      "name_ru": "Трапеции",     "name_en": "Traps",      "body_part": "upper"},
    {"code": "shoulders",  "name_ru": "Плечи",        "name_en": "Shoulders",  "body_part": "upper"},
    {"code": "biceps",     "name_ru": "Бицепс",       "name_en": "Biceps",     "body_part": "upper"},
    {"code": "triceps",    "name_ru": "Трицепс",      "name_en": "Triceps",    "body_part": "upper"},
    {"code": "forearms",   "name_ru": "Предплечья",   "name_en": "Forearms",   "body_part": "upper"},
    {"code": "quads",      "name_ru": "Квадрицепс",   "name_en": "Quads",      "body_part": "lower"},
    {"code": "hamstrings", "name_ru": "Бицепс бедра", "name_en": "Hamstrings", "body_part": "lower"},
    {"code": "glutes",     "name_ru": "Ягодицы",      "name_en": "Glutes",     "body_part": "lower"},
    {"code": "calves",     "name_ru": "Икры",         "name_en": "Calves",     "body_part": "lower"},
    {"code": "core",       "name_ru": "Кор / Пресс",  "name_en": "Core",       "body_part": "core"},
    {"code": "fullbody",   "name_ru": "Всё тело",     "name_en": "Full Body",  "body_part": "fullbody"},
]

EQUIPMENT_CATALOG = [
    {"code": "bodyweight",   "name_ru": "Собственный вес",    "name_en": "Bodyweight",       "category": "none",       "icon": "🤸"},
    {"code": "dumbbells",    "name_ru": "Гантели",            "name_en": "Dumbbells",         "category": "portable",   "icon": "🏋️"},
    {"code": "barbell",      "name_ru": "Штанга",             "name_en": "Barbell",           "category": "portable",   "icon": "🏋️"},
    {"code": "kettlebell",   "name_ru": "Гиря",               "name_en": "Kettlebell",        "category": "portable",   "icon": "⚫"},
    {"code": "resistance_band","name_ru": "Резинка",          "name_en": "Resistance Band",   "category": "portable",   "icon": "🔴"},
    {"code": "pull_up_bar",  "name_ru": "Турник",             "name_en": "Pull-up Bar",       "category": "portable",   "icon": "🔩"},
    {"code": "jump_rope",    "name_ru": "Скакалка",           "name_en": "Jump Rope",         "category": "portable",   "icon": "⭕"},
    {"code": "bench",        "name_ru": "Скамья",             "name_en": "Bench",             "category": "portable",   "icon": "🪑"},
    {"code": "dip_bars",     "name_ru": "Брусья",             "name_en": "Dip Bars",          "category": "portable",   "icon": "🤸"},
    {"code": "cable_machine","name_ru": "Блочный тренажёр",   "name_en": "Cable Machine",     "category": "stationary", "icon": "🏗"},
    {"code": "leg_press",    "name_ru": "Жим ногами",         "name_en": "Leg Press",         "category": "stationary", "icon": "🦵"},
    {"code": "smith_machine","name_ru": "Смит",               "name_en": "Smith Machine",     "category": "stationary", "icon": "🏋️"},
    {"code": "lat_pulldown", "name_ru": "Верхний блок",       "name_en": "Lat Pulldown",      "category": "stationary", "icon": "🔽"},
    {"code": "seated_row",   "name_ru": "Нижний блок",        "name_en": "Seated Row",        "category": "stationary", "icon": "🚣"},
    {"code": "leg_curl",     "name_ru": "Сгибание ног",       "name_en": "Leg Curl",          "category": "stationary", "icon": "🦵"},
    {"code": "leg_extension","name_ru": "Разгибание ног",     "name_en": "Leg Extension",     "category": "stationary", "icon": "🦵"},
    {"code": "crossover",    "name_ru": "Кроссовер",          "name_en": "Crossover",         "category": "stationary", "icon": "✖️"},
    {"code": "hack_squat",   "name_ru": "Гак-тренажёр",       "name_en": "Hack Squat",        "category": "stationary", "icon": "🦵"},
    {"code": "calf_raise_machine","name_ru": "Тренажёр икры", "name_en": "Calf Raise Machine","category": "stationary", "icon": "🦵"},
    {"code": "pec_deck",     "name_ru": "Бабочка",            "name_en": "Pec Deck",          "category": "stationary", "icon": "🦋"},
    {"code": "rowing_machine","name_ru": "Гребной тренажёр",  "name_en": "Rowing Machine",    "category": "stationary", "icon": "🚣"},
    {"code": "treadmill",    "name_ru": "Беговая дорожка",    "name_en": "Treadmill",         "category": "stationary", "icon": "🏃"},
    {"code": "stationary_bike","name_ru": "Велотренажёр",     "name_en": "Stationary Bike",   "category": "stationary", "icon": "🚴"},
    {"code": "elliptical",   "name_ru": "Эллипсоид",          "name_en": "Elliptical",        "category": "stationary", "icon": "⭕"},
]

ACHIEVEMENTS = [
    {"code": "first_workout",   "name": "Первый шаг",       "desc": "Завершил первую тренировку",           "icon": "👟", "cat": "consistency", "tier": "bronze",   "xp": 50,   "cond": {"type": "total_workouts", "value": 1}},
    {"code": "workouts_7",      "name": "Неделя силы",       "desc": "7 тренировок",                         "icon": "📅", "cat": "consistency", "tier": "bronze",   "xp": 100,  "cond": {"type": "total_workouts", "value": 7}},
    {"code": "workouts_30",     "name": "Месяц в зале",      "desc": "30 тренировок",                        "icon": "🏅", "cat": "consistency", "tier": "silver",   "xp": 300,  "cond": {"type": "total_workouts", "value": 30}},
    {"code": "workouts_100",    "name": "Сотка",             "desc": "100 тренировок",                       "icon": "💯", "cat": "consistency", "tier": "gold",     "xp": 1000, "cond": {"type": "total_workouts", "value": 100}},
    {"code": "streak_3",        "name": "3 подряд",          "desc": "3 тренировки без пропусков",           "icon": "🔥", "cat": "consistency", "tier": "bronze",   "xp": 75,   "cond": {"type": "streak", "value": 3}},
    {"code": "streak_7",        "name": "Огонь",             "desc": "7 тренировок подряд",                  "icon": "🔥", "cat": "consistency", "tier": "silver",   "xp": 200,  "cond": {"type": "streak", "value": 7}},
    {"code": "streak_30",       "name": "Несгораемый",       "desc": "30 дней подряд",                       "icon": "⚡", "cat": "consistency", "tier": "gold",     "xp": 500,  "cond": {"type": "streak", "value": 30}},
    {"code": "streak_100",      "name": "Легенда стрика",    "desc": "100 дней подряд",                      "icon": "🏆", "cat": "consistency", "tier": "platinum", "xp": 2000, "cond": {"type": "streak", "value": 100}},
    {"code": "pr_first",        "name": "Первый рекорд",     "desc": "Установил первый личный рекорд",       "icon": "🥇", "cat": "strength",    "tier": "bronze",   "xp": 75,   "cond": {"type": "pr_count", "value": 1}},
    {"code": "pr_10",           "name": "Рекордсмен",        "desc": "10 личных рекордов",                   "icon": "🏆", "cat": "strength",    "tier": "silver",   "xp": 250,  "cond": {"type": "pr_count", "value": 10}},
    {"code": "bench_bodyweight","name": "Жим своего веса",   "desc": "Жим лёжа = свой вес",                  "icon": "🎯", "cat": "strength",    "tier": "gold",     "xp": 500,  "cond": {"type": "exercise_ratio", "exercise": "bench_press", "ratio": 1.0}},
    {"code": "squat_1_5x",      "name": "Приседание 1.5x",   "desc": "Присед = 1.5x веса тела",              "icon": "🦵", "cat": "strength",    "tier": "gold",     "xp": 500,  "cond": {"type": "exercise_ratio", "exercise": "squat", "ratio": 1.5}},
    {"code": "deadlift_2x",     "name": "Двойной",           "desc": "Становая = 2x веса тела",              "icon": "💪", "cat": "strength",    "tier": "platinum", "xp": 1000, "cond": {"type": "exercise_ratio", "exercise": "deadlift", "ratio": 2.0}},
    {"code": "volume_1t",       "name": "Тонна",             "desc": "1000 кг за тренировку",                "icon": "💪", "cat": "volume",      "tier": "silver",   "xp": 200,  "cond": {"type": "session_volume", "value": 1000}},
    {"code": "volume_5t",       "name": "5 тонн",            "desc": "5000 кг за тренировку",                "icon": "💥", "cat": "volume",      "tier": "gold",     "xp": 500,  "cond": {"type": "session_volume", "value": 5000}},
    {"code": "total_10t",       "name": "10 тонн суммарно",  "desc": "10000 кг за все тренировки",           "icon": "🏋️", "cat": "volume",      "tier": "bronze",   "xp": 150,  "cond": {"type": "total_volume", "value": 10000}},
    {"code": "total_100t",      "name": "100 тонн",          "desc": "100 тонн суммарно",                    "icon": "🏋️", "cat": "volume",      "tier": "silver",   "xp": 300,  "cond": {"type": "total_volume", "value": 100000}},
    {"code": "total_1000t",     "name": "Машина",            "desc": "1000 тонн суммарно",                   "icon": "🤖", "cat": "volume",      "tier": "platinum", "xp": 2000, "cond": {"type": "total_volume", "value": 1000000}},
    {"code": "level_5",         "name": "Любитель",          "desc": "Уровень 5",                            "icon": "⭐", "cat": "milestone",   "tier": "bronze",   "xp": 100,  "cond": {"type": "level", "value": 5}},
    {"code": "level_10",        "name": "Атлет",             "desc": "Уровень 10",                           "icon": "⭐", "cat": "milestone",   "tier": "gold",     "xp": 500,  "cond": {"type": "level", "value": 10}},
    {"code": "level_20",        "name": "Зверь",             "desc": "Уровень 20",                           "icon": "⭐", "cat": "milestone",   "tier": "platinum", "xp": 1000, "cond": {"type": "level", "value": 20}},
    {"code": "early_bird",      "name": "Ранняя пташка",     "desc": "Тренировка до 7 утра",                 "icon": "🌅", "cat": "special",     "tier": "bronze",   "xp": 100,  "cond": {"type": "workout_before_hour", "value": 7}},
    {"code": "night_owl",       "name": "Сова",              "desc": "Тренировка после 22:00",               "icon": "🦉", "cat": "special",     "tier": "bronze",   "xp": 100,  "cond": {"type": "workout_after_hour", "value": 22}},
    {"code": "hard_mode_10",    "name": "Мазохист",          "desc": "10 тренировок в режиме хард",          "icon": "🔴", "cat": "special",     "tier": "silver",   "xp": 200,  "cond": {"type": "hard_sessions", "value": 10}},
    {"code": "comeback",        "name": "Камбэк",            "desc": "Вернулся после 2+ нед перерыва",       "icon": "🔙", "cat": "special",     "tier": "bronze",   "xp": 75,   "cond": {"type": "return_after_days", "value": 14}},
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Muscle groups
        existing_mg = {mg.code for mg in (await session.execute(select(MuscleGroup))).scalars()}
        for mg_data in MUSCLE_GROUPS:
            if mg_data["code"] not in existing_mg:
                session.add(MuscleGroup(**mg_data))
        await session.flush()

        # Equipment
        existing_eq = {e.code: e for e in (await session.execute(select(Equipment))).scalars()}
        eq_map = {}
        for eq_data in EQUIPMENT_CATALOG:
            if eq_data["code"] not in existing_eq:
                eq = Equipment(
                    code=eq_data["code"], name_ru=eq_data["name_ru"], name_en=eq_data["name_en"],
                    category=EquipmentCategory(eq_data["category"]), icon=eq_data.get("icon")
                )
                session.add(eq)
                await session.flush()
                eq_map[eq_data["code"]] = eq
            else:
                eq_map[eq_data["code"]] = existing_eq[eq_data["code"]]

        # Muscle group map
        mg_map = {mg.code: mg for mg in (await session.execute(select(MuscleGroup))).scalars()}

        # Exercises
        existing_ex = {e.code for e in (await session.execute(select(Exercise))).scalars()}
        for ex_data in EXERCISES:
            if ex_data["code"] in existing_ex:
                continue
            mg = mg_map.get(ex_data["muscle"])
            eq = eq_map.get(ex_data.get("equipment"))
            session.add(Exercise(
                code=ex_data["code"],
                name_ru=ex_data["name_ru"],
                name_en=ex_data["name_en"],
                primary_muscle_group_id=mg.id if mg else None,
                required_equipment_id=eq.id if eq else None,
                equipment_category=EquipmentCategory(ex_data["eq_cat"]),
                exercise_type=ExerciseType(ex_data["type"]),
                difficulty=ex_data["difficulty"],
                met_value=ex_data["met"],
                photo_url=ex_data["photo"],
                instructions=ex_data.get("instructions"),
                tips=ex_data.get("tips"),
                common_mistakes=ex_data.get("mistakes"),
                is_active=True,
            ))

        # Achievements
        existing_ach = {a.code for a in (await session.execute(select(Achievement))).scalars()}
        for a in ACHIEVEMENTS:
            if a["code"] not in existing_ach:
                session.add(Achievement(
                    code=a["code"], name=a["name"], description=a["desc"],
                    icon=a.get("icon"),
                    category=AchievementCategory(a["cat"]),
                    tier=AchievementTier(a["tier"]),
                    xp_reward=a["xp"],
                    condition=a["cond"],
                ))

        await session.commit()
        print(f"Seed complete: {len(MUSCLE_GROUPS)} MG, {len(EQUIPMENT_CATALOG)} EQ, {len(EXERCISES)} EX, {len(ACHIEVEMENTS)} ACH")


if __name__ == "__main__":
    asyncio.run(seed())
