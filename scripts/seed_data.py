"""
Seed script — combines all exercise data and populates all reference tables.
Run: python -m scripts.seed_data
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, text
from core.db import AsyncSessionLocal, engine, Base
from models.exercise import Equipment, MuscleGroup, Exercise, EquipmentCategory, ExerciseType
from models.gamification import Achievement, AchievementCategory, AchievementTier
from scripts.exercises_chest_back import EXERCISES_CHEST_BACK
from scripts.exercises_rest import EXERCISES_REST
from scripts.exercises_extra import ALL_EXTRA_EXERCISES
from scripts.exercises_new import EXERCISES_NEW


# ─── Reference: Equipment ─────────────────────────────────────────────────────
EQUIPMENT_DATA = [
    {"code": "barbell",    "name_ru": "Штанга",            "name_en": "Barbell",           "category": "stationary", "icon": "🏋️"},
    {"code": "dumbbell",   "name_ru": "Гантели",           "name_en": "Dumbbells",         "category": "portable",   "icon": "💪"},
    {"code": "kettlebell", "name_ru": "Гиря",              "name_en": "Kettlebell",        "category": "portable",   "icon": "⚙️"},
    {"code": "cable",      "name_ru": "Блочный тренажёр",  "name_en": "Cable Machine",     "category": "stationary", "icon": "🔗"},
    {"code": "machine",    "name_ru": "Тренажёр",          "name_en": "Machine",           "category": "stationary", "icon": "🤖"},
    {"code": "pullup_bar", "name_ru": "Турник",            "name_en": "Pull-up Bar",       "category": "stationary", "icon": "🔱"},
    {"code": "dip_bar",    "name_ru": "Брусья",            "name_en": "Dip Bar",           "category": "stationary", "icon": "⚡"},
    {"code": "bench",      "name_ru": "Скамья",            "name_en": "Bench",             "category": "stationary", "icon": "🪑"},
    {"code": "resistance_band", "name_ru": "Резинка",      "name_en": "Resistance Band",   "category": "portable",   "icon": "🔴"},
    {"code": "trx",        "name_ru": "TRX петли",         "name_en": "TRX Suspension",    "category": "portable",   "icon": "🟡"},
    {"code": "ab_wheel",   "name_ru": "Ролик для пресса",  "name_en": "Ab Wheel",         "category": "portable",   "icon": "⭕"},
    {"code": "jump_rope",  "name_ru": "Скакалка",          "name_en": "Jump Rope",         "category": "portable",   "icon": "🪢"},
    {"code": "box",        "name_ru": "Плиобокс",          "name_en": "Plyometric Box",    "category": "stationary", "icon": "📦"},
    {"code": "bodyweight", "name_ru": "Без оборудования",  "name_en": "Bodyweight",        "category": "none",       "icon": "🧍"},
]

# ─── Reference: Muscle Groups ─────────────────────────────────────────────────
MUSCLE_GROUP_DATA = [
    {"code": "chest",         "name_ru": "Грудь",                   "name_en": "Chest",         "body_part": "upper_body"},
    {"code": "upper_chest",   "name_ru": "Верхняя грудь",           "name_en": "Upper Chest",   "body_part": "upper_body"},
    {"code": "lower_chest",   "name_ru": "Нижняя грудь",            "name_en": "Lower Chest",   "body_part": "upper_body"},
    {"code": "lats",          "name_ru": "Широчайшие",              "name_en": "Lats",          "body_part": "upper_body"},
    {"code": "middle_back",   "name_ru": "Средняя часть спины",     "name_en": "Middle Back",   "body_part": "upper_body"},
    {"code": "lower_back",    "name_ru": "Поясница",                "name_en": "Lower Back",    "body_part": "upper_body"},
    {"code": "traps",         "name_ru": "Трапеции",                "name_en": "Trapezius",     "body_part": "upper_body"},
    {"code": "front_delts",   "name_ru": "Передние дельты",         "name_en": "Front Delts",   "body_part": "upper_body"},
    {"code": "side_delts",    "name_ru": "Боковые дельты",          "name_en": "Side Delts",    "body_part": "upper_body"},
    {"code": "rear_delts",    "name_ru": "Задние дельты",           "name_en": "Rear Delts",    "body_part": "upper_body"},
    {"code": "biceps",        "name_ru": "Бицепс",                  "name_en": "Biceps",        "body_part": "upper_body"},
    {"code": "triceps",       "name_ru": "Трицепс",                 "name_en": "Triceps",       "body_part": "upper_body"},
    {"code": "forearms",      "name_ru": "Предплечья",              "name_en": "Forearms",      "body_part": "upper_body"},
    {"code": "quadriceps",    "name_ru": "Квадрицепс",              "name_en": "Quadriceps",    "body_part": "lower_body"},
    {"code": "hamstrings",    "name_ru": "Бицепс бедра",            "name_en": "Hamstrings",    "body_part": "lower_body"},
    {"code": "glutes",        "name_ru": "Ягодицы",                 "name_en": "Glutes",        "body_part": "lower_body"},
    {"code": "calves",        "name_ru": "Икры",                    "name_en": "Calves",        "body_part": "lower_body"},
    {"code": "abs",           "name_ru": "Пресс",                   "name_en": "Abs",           "body_part": "core"},
    {"code": "obliques",      "name_ru": "Косые мышцы живота",      "name_en": "Obliques",      "body_part": "core"},
    {"code": "full_body",     "name_ru": "Всё тело",                "name_en": "Full Body",     "body_part": "full_body"},
]

# ─── Achievements ─────────────────────────────────────────────────────────────
ACHIEVEMENTS_DATA = [
    # Consistency
    {"code": "first_workout",    "name": "Первый шаг",         "icon": "👟", "description": "Выполни первую тренировку",      "category": "consistency", "tier": "bronze",   "xp_reward": 50,  "condition": {"type": "total_workouts", "value": 1}},
    {"code": "workouts_5",       "name": "Разминка",           "icon": "🔥", "description": "5 тренировок выполнено",         "category": "consistency", "tier": "bronze",   "xp_reward": 100, "condition": {"type": "total_workouts", "value": 5}},
    {"code": "workouts_10",      "name": "Втянулся",           "icon": "💪", "description": "10 тренировок выполнено",        "category": "consistency", "tier": "bronze",   "xp_reward": 150, "condition": {"type": "total_workouts", "value": 10}},
    {"code": "workouts_25",      "name": "Постоянство",        "icon": "📅", "description": "25 тренировок",                 "category": "consistency", "tier": "silver",   "xp_reward": 250, "condition": {"type": "total_workouts", "value": 25}},
    {"code": "workouts_50",      "name": "Полсотни",           "icon": "🥈", "description": "50 тренировок",                 "category": "consistency", "tier": "silver",   "xp_reward": 400, "condition": {"type": "total_workouts", "value": 50}},
    {"code": "workouts_100",     "name": "Сотник",             "icon": "💯", "description": "100 тренировок",                "category": "consistency", "tier": "gold",     "xp_reward": 750, "condition": {"type": "total_workouts", "value": 100}},
    {"code": "workouts_250",     "name": "Легенда зала",       "icon": "🏆", "description": "250 тренировок",                "category": "consistency", "tier": "platinum", "xp_reward": 2000,"condition": {"type": "total_workouts", "value": 250}},
    # Streaks
    {"code": "streak_3",         "name": "Три дня подряд",     "icon": "🔥", "description": "Стрик 3 дня",                   "category": "consistency", "tier": "bronze",   "xp_reward": 75,  "condition": {"type": "streak", "value": 3}},
    {"code": "streak_7",         "name": "Неделя без пропусков","icon": "📆","description": "Стрик 7 дней",                  "category": "consistency", "tier": "silver",   "xp_reward": 200, "condition": {"type": "streak", "value": 7}},
    {"code": "streak_14",        "name": "Две недели",         "icon": "⚡", "description": "Стрик 14 дней",                 "category": "consistency", "tier": "silver",   "xp_reward": 350, "condition": {"type": "streak", "value": 14}},
    {"code": "streak_30",        "name": "Железная воля",      "icon": "🔱", "description": "Стрик 30 дней",                 "category": "consistency", "tier": "gold",     "xp_reward": 700, "condition": {"type": "streak", "value": 30}},
    {"code": "streak_100",       "name": "Машина",             "icon": "🤖", "description": "Стрик 100 дней",                "category": "consistency", "tier": "platinum", "xp_reward": 3000,"condition": {"type": "streak", "value": 100}},
    # Volume
    {"code": "volume_1t",        "name": "Тонна железа",       "icon": "⚖️", "description": "Поднял суммарно 1 000 кг",     "category": "volume",      "tier": "bronze",   "xp_reward": 100, "condition": {"type": "total_volume", "value": 1000}},
    {"code": "volume_10t",       "name": "10 тонн",            "icon": "🏗",  "description": "Поднял суммарно 10 000 кг",    "category": "volume",      "tier": "silver",   "xp_reward": 300, "condition": {"type": "total_volume", "value": 10000}},
    {"code": "volume_50t",       "name": "50 тонн",            "icon": "🦍", "description": "Поднял суммарно 50 000 кг",    "category": "volume",      "tier": "gold",     "xp_reward": 800, "condition": {"type": "total_volume", "value": 50000}},
    {"code": "volume_session_5k","name": "5К за раз",          "icon": "💥", "description": "5 000 кг за одну тренировку",  "category": "volume",      "tier": "gold",     "xp_reward": 500, "condition": {"type": "session_volume", "value": 5000}},
    # Levels
    {"code": "level_5",          "name": "Опытный",            "icon": "⭐", "description": "Достигни 5-го уровня",          "category": "milestone",   "tier": "bronze",   "xp_reward": 100, "condition": {"type": "level", "value": 5}},
    {"code": "level_10",         "name": "Профессионал",       "icon": "🌟", "description": "Достигни 10-го уровня",         "category": "milestone",   "tier": "silver",   "xp_reward": 300, "condition": {"type": "level", "value": 10}},
    {"code": "level_20",         "name": "Мастер",             "icon": "💎", "description": "Достигни 20-го уровня",         "category": "milestone",   "tier": "gold",     "xp_reward": 1000,"condition": {"type": "level", "value": 20}},
    {"code": "level_50",         "name": "Элита",              "icon": "👑", "description": "Достигни 50-го уровня",         "category": "milestone",   "tier": "platinum", "xp_reward": 5000,"condition": {"type": "level", "value": 50}},
    # PRs
    {"code": "pr_1",             "name": "Первый рекорд",      "icon": "🏅", "description": "Установи первый личный рекорд", "category": "strength",    "tier": "bronze",   "xp_reward": 100, "condition": {"type": "pr_count", "value": 1}},
    {"code": "pr_10",            "name": "10 рекордов",        "icon": "🎯", "description": "10 личных рекордов",            "category": "strength",    "tier": "silver",   "xp_reward": 300, "condition": {"type": "pr_count", "value": 10}},
    {"code": "pr_25",            "name": "Рекордсмен",         "icon": "🏆", "description": "25 личных рекордов",            "category": "strength",    "tier": "gold",     "xp_reward": 750, "condition": {"type": "pr_count", "value": 25}},
    # Special
    {"code": "early_bird",       "name": "Ранняя пташка",      "icon": "🌅", "description": "Тренировка до 7 утра",          "category": "special",     "tier": "silver",   "xp_reward": 200, "condition": {"type": "workout_before_hour", "value": 7}},
    {"code": "night_owl",        "name": "Сова",               "icon": "🦉", "description": "Тренировка после 22:00",        "category": "special",     "tier": "bronze",   "xp_reward": 150, "condition": {"type": "workout_after_hour", "value": 22}},
    {"code": "comeback",         "name": "Возвращение",        "icon": "🦅", "description": "Вернулся после 30+ дней паузы", "category": "special",     "tier": "gold",     "xp_reward": 500, "condition": {"type": "return_after_days", "value": 30}},
]


async def insert_or_update(session, model_class, unique_field, items):
    count_new = 0
    for item_data in items:
        res = await session.execute(
            select(model_class).where(getattr(model_class, unique_field) == item_data[unique_field])
        )
        existing = res.scalar_one_or_none()
        if not existing:
            session.add(model_class(**item_data))
            count_new += 1
        else:
            for k, v in item_data.items():
                setattr(existing, k, v)
    await session.commit()
    return count_new


async def seed_exercises(session, equipment_map, muscle_map):
    """Seed all exercises from all source files."""
    all_exercises = EXERCISES_CHEST_BACK + EXERCISES_REST + ALL_EXTRA_EXERCISES
    count_new = 0
    for ex in all_exercises:
        res = await session.execute(select(Exercise).where(Exercise.code == ex["code"]))
        existing = res.scalar_one_or_none()

        muscle_code = ex.get("muscle")
        muscle_id = muscle_map.get(muscle_code)
        eq_code = ex.get("equipment")
        eq_id = equipment_map.get(eq_code) if eq_code else None

        # Determine equipment_category
        if not eq_code:
            eq_cat = EquipmentCategory.none
        elif eq_code in ("barbell", "dumbbell", "cable", "machine", "pullup_bar", "dip_bar", "bench", "box"):
            eq_cat = EquipmentCategory.stationary
        else:
            eq_cat = EquipmentCategory.portable

        ex_type_map = {"compound": ExerciseType.compound, "isolation": ExerciseType.isolation,
                       "cardio": ExerciseType.cardio, "mobility": ExerciseType.mobility}
        ex_type = ex_type_map.get(ex.get("type", "compound"), ExerciseType.compound)

        fields = {
            "code": ex["code"],
            "name_ru": ex["name_ru"],
            "name_en": ex["name_en"],
            "description": ex.get("description"),
            "instructions": ex.get("instructions"),
            "tips": ex.get("tips"),
            "common_mistakes": ex.get("common_mistakes"),
            "primary_muscle_group_id": muscle_id,
            "required_equipment_id": eq_id,
            "equipment_category": eq_cat,
            "exercise_type": ex_type,
            "difficulty": ex.get("difficulty", 3),
            "met_value": ex.get("met_value"),
            "gif_url": ex.get("gif_url"),
            "photo_url": ex.get("photo_url"),
            "is_active": True,
        }

        if not existing:
            session.add(Exercise(**fields))
            count_new += 1
        else:
            for k, v in fields.items():
                setattr(existing, k, v)

    await session.commit()
    return count_new


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        print("Seeding equipment...")
        eq_data = [{k: v for k, v in e.items() if k != "icon"} for e in EQUIPMENT_DATA]
        for item in EQUIPMENT_DATA:
            d = {"code": item["code"], "name_ru": item["name_ru"], "name_en": item["name_en"],
                 "category": EquipmentCategory(item["category"]), "icon": item.get("icon")}
            res = await session.execute(select(Equipment).where(Equipment.code == item["code"]))
            existing = res.scalar_one_or_none()
            if not existing:
                session.add(Equipment(**d))
            else:
                for k, v in d.items():
                    setattr(existing, k, v)
        await session.commit()

        print("Seeding muscle groups...")
        for item in MUSCLE_GROUP_DATA:
            res = await session.execute(select(MuscleGroup).where(MuscleGroup.code == item["code"]))
            existing = res.scalar_one_or_none()
            if not existing:
                session.add(MuscleGroup(**item))
            else:
                for k, v in item.items():
                    setattr(existing, k, v)
        await session.commit()

        # Build lookup maps
        eq_res = await session.execute(select(Equipment))
        equipment_map = {e.code: e.id for e in eq_res.scalars()}
        mg_res = await session.execute(select(MuscleGroup))
        muscle_map = {m.code: m.id for m in mg_res.scalars()}

        print("Seeding exercises...")
        new_ex = await seed_exercises(session, equipment_map, muscle_map)
        total = len(EXERCISES_CHEST_BACK) + len(EXERCISES_REST) + len(ALL_EXTRA_EXERCISES)
        print(f"  Exercises: {total} total, {new_ex} new")

        print("Seeding achievements...")
        for item in ACHIEVEMENTS_DATA:
            d = {
                "code": item["code"], "name": item["name"], "icon": item["icon"],
                "description": item["description"],
                "category": AchievementCategory(item["category"]),
                "tier": AchievementTier(item["tier"]),
                "xp_reward": item["xp_reward"],
                "condition": item["condition"],
            }
            res = await session.execute(select(Achievement).where(Achievement.code == item["code"]))
            existing = res.scalar_one_or_none()
            if not existing:
                session.add(Achievement(**d))
            else:
                for k, v in d.items():
                    setattr(existing, k, v)
        await session.commit()
        print(f"  Achievements: {len(ACHIEVEMENTS_DATA)}")

        print("\n✅ Seed complete!")


if __name__ == "__main__":
    asyncio.run(main())
